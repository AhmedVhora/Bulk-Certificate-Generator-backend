import pytest

from certificates.models import Certificate, CertificateJob


@pytest.mark.django_db
def test_create_job_creates_rows_and_returns_summary(api_client, valid_payload):
    response = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")

    assert response.status_code == 201
    job = CertificateJob.objects.get(pk=response.data["id"])
    assert job.total_count == 2
    assert job.success_count == 2
    assert job.failed_count == 0
    assert job.status == CertificateJob.Status.COMPLETED
    assert Certificate.objects.filter(job=job).count() == 2
    assert len(response.data["certificates"]) == 2
