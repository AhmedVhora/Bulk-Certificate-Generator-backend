from unittest.mock import patch

import pytest

from certificates.models import Certificate, CertificateJob


@pytest.mark.django_db
def test_one_generation_failure_does_not_stop_other_recipients(api_client, valid_payload):
    from certificates.services.certificate_service import render_certificate_pdf as real_renderer

    def renderer_that_fails_for_ravi(**kwargs):
        if kwargs["recipient_name"] == "Ravi Kumar":
            raise RuntimeError("renderer outage")
        return real_renderer(**kwargs)

    with patch(
        "certificates.services.certificate_service.render_certificate_pdf",
        side_effect=renderer_that_fails_for_ravi,
    ):
        response = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")

    assert response.status_code == 201
    job = CertificateJob.objects.get(pk=response.data["id"])
    failed = Certificate.objects.get(job=job, recipient_name="Ravi Kumar")
    succeeded = Certificate.objects.get(job=job, recipient_name="Asha Rao")
    assert job.status == CertificateJob.Status.COMPLETED_WITH_ERRORS
    assert (job.success_count, job.failed_count) == (1, 1)
    assert failed.status == Certificate.Status.FAILED
    assert failed.error_message
    assert succeeded.status == Certificate.Status.SUCCESS
