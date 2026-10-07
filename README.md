# Bulk Certificate Generator API

A Django REST Framework API that accepts one bulk request, creates a fixed-layout PDF certificate for every recipient, and records the independent result of every generation attempt.

## Setup

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
```

Configure `.env` as appropriate. SQLite is used by default. To switch to PostgreSQL without application code changes, set `DATABASE_URL`, for example:

```text
DATABASE_URL=postgres://user:password@localhost:5432/certificates
```

Start the service:

```powershell
python manage.py runserver
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/api/docs/`.

## Tests

```powershell
pytest
```

Tests use a temporary `MEDIA_ROOT`, so generated files do not leak into the repository.

## API usage

Create and process a job:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/certificate-jobs/ `
  -H "Content-Type: application/json" `
  -d '{"event_name":"Django Bootcamp 2026","issue_date":"2026-10-07","issued_by":"Acme Academy","recipients":[{"name":"Asha Rao","email":"asha@example.com"},{"name":"Ravi Kumar","email":"ravi@example.com"}]}'
```

The response is `201 Created` and includes its UUID and each certificate's outcome. Check it later (or immediately, since this implementation is synchronous):

```powershell
curl.exe http://127.0.0.1:8000/api/v1/certificate-jobs/<job-id>/
```

Download one successful certificate or all successful files from a job:

```powershell
curl.exe -OJ http://127.0.0.1:8000/api/v1/certificates/<certificate-id>/download/
curl.exe -OJ http://127.0.0.1:8000/api/v1/certificate-jobs/<job-id>/download/
```

## Architecture

```
config/                         Django settings and root URLs
certificates/
  models.py                     CertificateJob and Certificate persistence
  serializers.py                Request validation and response shape
  services/job_service.py       Bulk job orchestration and final counts
  services/certificate_service.py  Single-certificate storage and state updates
  generators/pdf_generator.py   Pure ReportLab PDF renderer
  views.py                      Thin HTTP endpoints only
```

- **Serializers** validate every request field before a job exists.
- **Services** own database mutation, workflow, logging, and per-recipient isolation.
- **Generator** is a pure function that takes certificate values and returns PDF bytes; it has no database or HTTP knowledge.
- **Views** only validate, call a service, serialize, or stream a file.

## Design decisions

**Synchronous processing.** Generation happens inside the create request. This keeps deployment simple—no broker or worker is required—and is suitable for the assignment's scale of hundreds of recipients. `MAX_RECIPIENTS_PER_JOB` (default `500`) prevents an unbounded request.

**Invalid versus failed recipients.** Input validation is all-or-nothing: one invalid recipient rejects the whole payload with `400 Bad Request` and precise per-item errors. Once a valid job is accepted, a ReportLab or storage failure affects only that certificate; it is marked `FAILED` with a safe message while remaining recipients continue. The job becomes `COMPLETED_WITH_ERRORS` if some succeed, or `FAILED` if all fail.

**Template and storage.** ReportLab produces the one code-defined A4 landscape template (border, heading, recipient, event, issue date, and issuer). Files are stored using Django's configured default storage, locally under `MEDIA_ROOT` by default. That keeps the renderer pure and lets production switch to an S3-compatible storage backend through settings.

## Limitations and next steps

For thousands of recipients, move the loop in `job_service.py` into a Celery task backed by Redis; the separation of the service layer makes that a localized change. Production deployments should also add S3/object storage, retry policies, authentication/authorization, rate limiting, observability, and pagination for large job-status responses.
