from datetime import date

import pytest

from certificates.generators.pdf_generator import render_certificate_pdf
from certificates.models import Certificate


@pytest.mark.django_db
def test_generator_returns_pdf_and_processing_saves_file(api_client, valid_payload):
    pdf = render_certificate_pdf(
        recipient_name="Asha Rao",
        event_name="Django Bootcamp",
        issue_date=date(2026, 10, 7),
        issued_by="Acme Academy",
    )

    response = api_client.post("/api/v1/certificate-jobs/", valid_payload, format="json")

    assert pdf.startswith(b"%PDF")
    assert response.status_code == 201
    certificates = Certificate.objects.order_by("recipient_name")
    assert certificates.count() == 2
    assert all(certificate.file.storage.exists(certificate.file.name) for certificate in certificates)
    assert all(certificate.status == Certificate.Status.SUCCESS for certificate in certificates)
