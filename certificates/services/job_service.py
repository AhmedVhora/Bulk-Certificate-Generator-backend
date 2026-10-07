"""Orchestrate creation and synchronous processing of a bulk job."""

import logging
from typing import Any

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from certificates.models import Certificate, CertificateJob
from certificates.services.certificate_service import generate_certificate


logger = logging.getLogger(__name__)


def create_and_process_job(validated_data: dict[str, Any]) -> CertificateJob:
    """Create a job and all rows, then independently generate every PDF."""
    recipients = validated_data.pop("recipients")
    with transaction.atomic():
        job = CertificateJob.objects.create(
            **validated_data,
            total_count=len(recipients),
            status=CertificateJob.Status.PENDING,
        )
        Certificate.objects.bulk_create([
            Certificate(
                job=job,
                recipient_name=recipient["name"],
                recipient_email=recipient["email"],
            )
            for recipient in recipients
        ])

    CertificateJob.objects.filter(pk=job.pk).update(
        status=CertificateJob.Status.PROCESSING,
        updated_at=timezone.now(),
    )
    certificates = Certificate.objects.filter(job=job).select_related("job")
    for certificate in certificates:
        try:
            generate_certificate(certificate)
        except Exception:  # Keep isolation even if a service implementation changes.
            logger.exception("Unexpected processing failure for certificate %s", certificate.id)
            Certificate.objects.filter(pk=certificate.pk).update(
                status=Certificate.Status.FAILED,
                error_message="Certificate generation could not be completed.",
            )

    counts = Certificate.objects.filter(job=job).aggregate(
        succeeded=Count("id", filter=Q(status=Certificate.Status.SUCCESS)),
        failed=Count("id", filter=Q(status=Certificate.Status.FAILED)),
    )
    succeeded = counts["succeeded"]
    failed = counts["failed"]
    final_status = _final_job_status(success_count=succeeded, failed_count=failed)
    CertificateJob.objects.filter(pk=job.pk).update(
        status=final_status,
        success_count=succeeded,
        failed_count=failed,
        updated_at=timezone.now(),
    )
    return CertificateJob.objects.prefetch_related("certificates").get(pk=job.pk)


def _final_job_status(*, success_count: int, failed_count: int) -> str:
    """Map final per-certificate outcomes to the job's terminal state."""
    if failed_count == 0:
        return CertificateJob.Status.COMPLETED
    if success_count == 0:
        return CertificateJob.Status.FAILED
    return CertificateJob.Status.COMPLETED_WITH_ERRORS
