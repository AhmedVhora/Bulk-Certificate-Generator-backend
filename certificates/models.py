"""Database models for certificate jobs and their output files."""

import uuid

from django.db import models

from .constants import (
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_EVENT_NAME_LENGTH,
    MAX_ISSUER_NAME_LENGTH,
    MAX_RECIPIENT_NAME_LENGTH,
)


class CertificateJob(models.Model):
    """A bulk request to create certificates from the fixed template."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS", "Completed with errors"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=MAX_EVENT_NAME_LENGTH)
    issue_date = models.DateField()
    issued_by = models.CharField(max_length=MAX_ISSUER_NAME_LENGTH)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    total_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("status", "created_at"))]

    def __str__(self) -> str:
        return f"{self.event_name} ({self.id})"


class Certificate(models.Model):
    """One recipient's certificate, including any generation failure."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(CertificateJob, on_delete=models.CASCADE, related_name="certificates")
    recipient_name = models.CharField(max_length=MAX_RECIPIENT_NAME_LENGTH)
    recipient_email = models.EmailField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.CharField(max_length=MAX_ERROR_MESSAGE_LENGTH, blank=True)
    file = models.FileField(upload_to="certificates/%Y/%m/%d/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=("job", "status")),
            models.Index(fields=("status",)),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_name} - {self.job.event_name}"
