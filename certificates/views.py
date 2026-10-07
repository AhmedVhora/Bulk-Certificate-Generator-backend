"""Thin HTTP layer for certificate operations."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import CertificateUnavailable
from .models import Certificate, CertificateJob
from .serializers import CertificateJobOutputSerializer, CreateJobSerializer
from .services.job_service import create_and_process_job


class CertificateJobListCreateView(APIView):
    """Accept and synchronously process a bulk certificate generation job."""

    def post(self, request):
        serializer = CreateJobSerializer(
            data=request.data,
            context={"max_recipients": settings.MAX_RECIPIENTS_PER_JOB},
        )
        serializer.is_valid(raise_exception=True)
        job = create_and_process_job(serializer.validated_data)
        return Response(
            CertificateJobOutputSerializer(job, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CertificateJobDetailView(APIView):
    """Return a job's current result, including every certificate outcome."""

    def get(self, request, job_id):
        job = get_object_or_404(
            CertificateJob.objects.prefetch_related("certificates"), pk=job_id
        )
        return Response(CertificateJobOutputSerializer(job, context={"request": request}).data)


class CertificateDownloadView(APIView):
    """Download one successfully generated PDF."""

    def get(self, request, certificate_id):
        certificate = get_object_or_404(
            Certificate.objects.select_related("job"), pk=certificate_id
        )
        if certificate.status != Certificate.Status.SUCCESS or not certificate.file:
            raise CertificateUnavailable()
        try:
            return FileResponse(
                certificate.file.open("rb"),
                as_attachment=True,
                filename=f"certificate-{certificate.id}.pdf",
                content_type="application/pdf",
            )
        except FileNotFoundError as exc:
            raise Http404("Certificate file was not found.") from exc


class CertificateJobZipDownloadView(APIView):
    """Package all available successful PDFs of a job into one ZIP archive."""

    def get(self, request, job_id):
        job = get_object_or_404(CertificateJob, pk=job_id)
        archive = BytesIO()
        successful_certificates = Certificate.objects.filter(
            job=job, status=Certificate.Status.SUCCESS
        )
        with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
            for certificate in successful_certificates:
                if not certificate.file:
                    continue
                try:
                    with certificate.file.open("rb") as pdf_file:
                        zip_file.writestr(
                            f"certificate-{certificate.id}.pdf", pdf_file.read()
                        )
                except FileNotFoundError:
                    continue
        filename = f"{slugify(job.event_name) or 'certificates'}-{job.id}.zip"
        response = HttpResponse(archive.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
