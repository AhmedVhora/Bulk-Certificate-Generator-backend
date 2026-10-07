import pytest
from django.conf import settings


URL = "/api/v1/certificate-jobs/"


@pytest.mark.django_db
def test_missing_required_field_returns_clear_400(api_client, valid_payload):
    valid_payload.pop("event_name")

    response = api_client.post(URL, valid_payload, format="json")

    assert response.status_code == 400
    assert "event_name" in response.data["error"]["details"]


@pytest.mark.django_db
def test_invalid_email_and_blank_name_return_per_item_errors(api_client, valid_payload):
    valid_payload["recipients"] = [{"name": "   ", "email": "not-an-email"}]

    response = api_client.post(URL, valid_payload, format="json")

    assert response.status_code == 400
    recipient_errors = response.data["error"]["details"]["recipients"][0]
    assert "name" in recipient_errors
    assert "email" in recipient_errors


@pytest.mark.django_db
def test_empty_recipient_list_is_rejected(api_client, valid_payload):
    valid_payload["recipients"] = []

    response = api_client.post(URL, valid_payload, format="json")

    assert response.status_code == 400
    assert "recipients" in response.data["error"]["details"]


@pytest.mark.django_db
def test_oversized_recipient_list_is_rejected(api_client, valid_payload, settings):
    settings.MAX_RECIPIENTS_PER_JOB = 2
    valid_payload["recipients"].append({"name": "Third Person", "email": "third@example.com"})

    response = api_client.post(URL, valid_payload, format="json")

    assert response.status_code == 400
    assert "at most 2" in str(response.data["error"]["details"])
