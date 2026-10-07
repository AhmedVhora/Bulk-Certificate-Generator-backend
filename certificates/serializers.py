"""Input validation and response serialization for the public API."""

from rest_framework import serializers

from .constants import MAX_EVENT_NAME_LENGTH, MAX_ISSUER_NAME_LENGTH, MAX_RECIPIENT_NAME_LENGTH
from .models import Certificate, CertificateJob


class RecipientSerializer(serializers.Serializer):
    """Validate an individual recipient before any job is created."""

    name = serializers.CharField(max_length=MAX_RECIPIENT_NAME_LENGTH, trim_whitespace=True)
    email = serializers.EmailField()

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Recipient name must not be blank.")
        return value


class CreateJobSerializer(serializers.Serializer):
    """Validate a full, all-or-nothing job submission payload."""

    event_name = serializers.CharField(max_length=MAX_EVENT_NAME_LENGTH, trim_whitespace=True)
    issue_date = serializers.DateField()
    issued_by = serializers.CharField(max_length=MAX_ISSUER_NAME_LENGTH, trim_whitespace=True)
    recipients = RecipientSerializer(many=True, allow_empty=False)

    def validate_event_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Event name must not be blank.")
        return value

    def validate_issued_by(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Issuer name must not be blank.")
        return value

    def validate_recipients(self, recipients: list[dict]) -> list[dict]:
        max_recipients = self.context["max_recipients"]
        if len(recipients) > max_recipients:
            raise serializers.ValidationError(
                f"A job may contain at most {max_recipients} recipients."
            )
        return recipients


class CertificateOutputSerializer(serializers.ModelSerializer):
    """Expose an individual certificate's state without exposing storage paths."""

    download_url = serializers.SerializerMethodField()
    error_message = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ("id", "recipient_name", "recipient_email", "status", "download_url", "error_message")

    def get_download_url(self, certificate: Certificate) -> str | None:
        if certificate.status != Certificate.Status.SUCCESS or not certificate.file:
            return None
        request = self.context.get("request")
        relative_url = f"/api/v1/certificates/{certificate.id}/download/"
        return request.build_absolute_uri(relative_url) if request else relative_url

    def get_error_message(self, certificate: Certificate) -> str | None:
        return certificate.error_message or None


class CertificateJobOutputSerializer(serializers.ModelSerializer):
    """Return a job summary and each certificate outcome."""

    certificates = CertificateOutputSerializer(many=True, read_only=True)

    class Meta:
        model = CertificateJob
        fields = (
            "id",
            "event_name",
            "issue_date",
            "issued_by",
            "status",
            "total_count",
            "success_count",
            "failed_count",
            "created_at",
            "updated_at",
            "certificates",
        )
