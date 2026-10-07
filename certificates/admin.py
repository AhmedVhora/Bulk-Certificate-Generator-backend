"""Django admin configuration."""

from django.contrib import admin

from .models import Certificate, CertificateJob


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0
    readonly_fields = ("id", "recipient_name", "recipient_email", "status", "error_message", "file")
    can_delete = False


@admin.register(CertificateJob)
class CertificateJobAdmin(admin.ModelAdmin):
    list_display = ("id", "event_name", "status", "total_count", "success_count", "failed_count", "created_at")
    list_filter = ("status",)
    search_fields = ("event_name", "issued_by")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (CertificateInline,)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient_name", "recipient_email", "job", "status")
    list_filter = ("status",)
    search_fields = ("recipient_name", "recipient_email")
    readonly_fields = ("id", "created_at")
