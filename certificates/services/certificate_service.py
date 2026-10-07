"""Generate and persist a single certificate."""

import logging

from django.core.files.base import ContentFile

from certificates.constants import DEFAULT_CERTIFICATE_FILENAME_PREFIX
from certificates.generators.pdf_generator import render_certificate_pdf
from certificates.models import Certificate


logger = logging.getLogger(__name__)


def generate_certificate(certificate: Certificate) -> None:
    """Render, store, and mark one certificate without raising expected errors.

    Any renderer or storage failure is recorded against this certificate so the
    surrounding job can continue processing its remaining recipients.
    """
    try:
        pdf_bytes = render_certificate_pdf(
            recipient_name=certificate.recipient_name,
            event_name=certificate.job.event_name,
            issue_date=certificate.job.issue_date,
            issued_by=certificate.job.issued_by,
        )
        filename = f"{DEFAULT_CERTIFICATE_FILENAME_PREFIX}-{certificate.id}.pdf"
        certificate.file.save(filename, ContentFile(pdf_bytes), save=False)
        certificate.status = Certificate.Status.SUCCESS
        certificate.error_message = ""
        certificate.save(update_fields=("file", "status", "error_message"))
    except Exception as exc:  # Defensive boundary around external rendering/storage work.
        logger.exception("Certificate generation failed for certificate %s", certificate.id)
        certificate.status = Certificate.Status.FAILED
        certificate.error_message = "Certificate generation could not be completed."
        certificate.save(update_fields=("status", "error_message"))
