import shutil
from pathlib import Path

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def temporary_media_root(settings) -> None:
    """Keep generated test files in a disposable directory outside media/."""
    media_root = Path(settings.BASE_DIR) / "test-media"
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = media_root
    yield
    shutil.rmtree(media_root, ignore_errors=True)


@pytest.fixture
def valid_payload() -> dict:
    return {
        "event_name": "Django Bootcamp 2026",
        "issue_date": "2026-10-07",
        "issued_by": "Acme Academy",
        "recipients": [
            {"name": "Asha Rao", "email": "asha@example.com"},
            {"name": "Ravi Kumar", "email": "ravi@example.com"},
        ],
    }
