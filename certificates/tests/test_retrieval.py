from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

import pytest

from certificates.models import Certificate, CertificateJob


@pytest.mark.django_db
def test_single_pdf_and_zip_downloads_include_successful_files(api_client, valid_payload):
    created = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")
    certificate_id = created.data["certificates"][0]["id"]

    pdf_response = api_client.get(f"/api/v1/certificates/{certificate_id}/download/")
    zip_response = api_client.get(f"/api/v1/certificate-jobs/{created.data['id']}/download/")

    assert pdf_response.status_code == 200
    assert b"".join(pdf_response.streaming_content).startswith(b"%PDF")
    assert zip_response.status_code == 200
    with ZipFile(BytesIO(zip_response.content)) as archive:
        assert len(archive.namelist()) == 2
        assert all(archive.read(name).startswith(b"%PDF") for name in archive.namelist())


@pytest.mark.django_db
def test_failed_and_unknown_certificate_downloads_return_appropriate_errors(api_client, valid_payload):
    with patch(
        "certificates.services.certificate_service.render_certificate_pdf",
        side_effect=RuntimeError("renderer unavailable"),
    ):
        created = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")
    failed_id = created.data["certificates"][0]["id"]

    failed_response = api_client.get(f"/api/v1/certificates/{failed_id}/download/")
    missing_response = api_client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download/")

    assert failed_response.status_code == 409
    assert failed_response.data["error"]["code"] == "certificate_unavailable"
    assert missing_response.status_code == 404
