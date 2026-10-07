import pytest

from certificates.models import CertificateJob


@pytest.mark.django_db
def test_job_status_returns_counts_and_certificate_details(api_client, valid_payload):
    created = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")

    response = api_client.get(f"/api/v1/certificate-jobs/{created.data['id']}/")

    assert response.status_code == 200
    assert response.data["status"] == CertificateJob.Status.COMPLETED
    assert response.data["total_count"] == 2
    assert response.data["success_count"] == 2
    assert response.data["failed_count"] == 0
    assert all(item["download_url"] for item in response.data["certificates"])
