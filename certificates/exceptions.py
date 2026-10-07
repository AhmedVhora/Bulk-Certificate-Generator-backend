"""Domain API exceptions and a consistent DRF error response envelope."""

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class CertificateUnavailable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This certificate was not generated successfully and cannot be downloaded."
    default_code = "certificate_unavailable"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Any:
    """Wrap handled DRF errors in a stable ``error`` payload."""
    response = exception_handler(exc, context)
    if response is not None:
        details = response.data
        default_detail = getattr(exc, "default_detail", None)
        message = str(default_detail) if default_detail else "Request could not be completed."
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": message,
                "details": details,
            }
        }
    return response
