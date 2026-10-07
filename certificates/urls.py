"""Version-one certificate API routes."""

from django.urls import path

from .views import (
    CertificateDownloadView,
    CertificateJobDetailView,
    CertificateJobListCreateView,
    CertificateJobZipDownloadView,
)


urlpatterns = [
    path("certificate-jobs/", CertificateJobListCreateView.as_view(), name="certificate-job-list"),
    path("certificate-jobs/<uuid:job_id>/", CertificateJobDetailView.as_view(), name="certificate-job-detail"),
    path("certificate-jobs/<uuid:job_id>/download/", CertificateJobZipDownloadView.as_view(), name="certificate-job-download"),
    path("certificates/<uuid:certificate_id>/download/", CertificateDownloadView.as_view(), name="certificate-download"),
]
