# API Reference

Base URL: `http://localhost:8001`
Interactive docs: `http://localhost:8001/docs` (Swagger UI)

---

## Health

### `GET /api/v1/health`
Health check endpoint.

**Response:**
```json
{"status": "healthy", "version": "1.0.0"}
```

---

## Candidates (`app/routers/candidates.py`)

### `POST /api/v1/candidates/upload`
Upload a CV file. Accepts `multipart/form-data`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF or DOCX (max 50MB) |
| `job_profile_id` | string | No | Associated job profile UUID |
| `recruiter_notes` | string | No | Notes from recruiter |

**Response:** `CandidateRead` (201)

### `GET /api/v1/candidates`
List all candidates with pagination.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Offset |
| `limit` | int | 50 | Max results |

**Response:** `List[CandidateRead]`

### `GET /api/v1/candidates/{candidate_id}`
Get a single candidate by ID.

**Response:** `CandidateRead`

### `DELETE /api/v1/candidates/{candidate_id}`
Delete a candidate and all associated data (files, records).

**Response:** 204 No Content

---

## Processing (`app/routers/processing.py`)

### `POST /api/v1/candidates/{candidate_id}/extract`
Trigger AI extraction for a candidate. Runs as a background task.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `instructions` | string (query) | null | Custom extraction instructions |

**Response:**
```json
{"task_id": "bg-<uuid>", "candidate_id": "<uuid>", "status": "queued"}
```

Allowed statuses for extraction: `UPLOADED`, `FAILED`, `EXTRACTED`, `PENDING_REVIEW`, `APPROVED`.

### `GET /api/v1/candidates/{candidate_id}/status`
Poll extraction status and progress.

**Response:**
```json
{
  "id": "<uuid>",
  "status": "EXTRACTED",
  "needs_review": true,
  "progress_pct": 60,
  "current_step": "EXTRACTED",
  "extraction_provider": "OpenAI",
  "extraction_model": "gpt-4o",
  "error": null
}
```

---

## Review (`app/routers/review.py`)

### `GET /api/v1/candidates/{candidate_id}/review`
Get extracted data for review: candidate info, employment history, skills, languages.

**Response:**
```json
{
  "candidate": {"id": "...", "full_name": "...", "status": "EXTRACTED", "needs_review": true},
  "employment_history": [{"id": "...", "company_name": "...", "job_title": "...", ...}],
  "skills": [{"id": "...", "skill_name": "...", "level": "Expert", ...}],
  "languages": [{"id": "...", "language": "Deutsch", "level_normalized": "B1", ...}],
  "needs_review_count": 3
}
```

### `PATCH /api/v1/candidates/{candidate_id}/review`
Update reviewed data. Accepts JSON body with:

```json
{
  "full_name": "Updated Name",
  "nationality": "Polish",
  "employment_updates": [
    {"id": "<uuid>", "gap_type": "career_break", "gap_note": "Parental leave", "needs_review": false}
  ]
}
```

### `POST /api/v1/candidates/{candidate_id}/approve`
Approve a candidate for template generation. Only works when status is `EXTRACTED` and all review items are resolved.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `approved_by` | string (query) | "recruiter" | Approver identifier |

**Response:**
```json
{"status": "approved", "approved_by": "recruiter"}
```

---

## Extraction (`app/routers/extraction.py`)

### `POST /api/v1/extraction/process`
End-to-end extraction: upload template + CV → AI extraction → populate template → return download link.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template` | File | Yes | Word template (.docx) |
| `cv_file` | File | Yes | CV (PDF/DOCX/JPEG) |
| `instructions` | string | No | Custom extraction instructions |
| `ai_model` | string | No | AI model name (default: gpt-4o) |

**Response:**
```json
{
  "task_id": "abc12345",
  "status": "completed",
  "candidate_name": "John Doe",
  "download_url": "/api/v1/extraction/download/abc12345"
}
```

### `GET /api/v1/extraction/status/{task_id}`
Check extraction task status.

### `GET /api/v1/extraction/preview/{task_id}`
Preview extracted JSON data before downloading the document.

### `GET /api/v1/extraction/download/{task_id}`
Download the populated DOCX file.

---

## Templates (`app/routers/templates.py`)

### `GET /api/v1/templates/`
List all templates.

**Response:** `List[TemplateSchema]`

### `POST /api/v1/templates/upload`
Upload a new Word template.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Template file (.docx) |
| `template_type` | string | No | Type: "lebenslauf" (default), "anschreiben", "zeugnis" |

### `PATCH /api/v1/templates/{id}/active`
Set a template as the active one (deactivates all others).

### `DELETE /api/v1/templates/{id}`
Delete a template and its file.

---

## Downloads (`app/routers/downloads.py`)

### `GET /api/v1/candidates/{candidate_id}/download/structured-cv`
Download the structured CV (DOCX populated with extracted data).

### `GET /api/v1/candidates/{candidate_id}/download/final-cv`
Download the final CV (only available after Stage 2 completion).

### `POST /api/v1/identcheck/{document_id}/confirm-download`
Confirm and export an identity document after verification.

---

## Settings (`app/routers/settings_router.py`)

### `GET /api/v1/settings/providers`
List all configured AI providers.

### `POST /api/v1/settings/providers`
Create a new AI provider.

**Body:**
```json
{
  "provider_type": "OPENAI",
  "display_name": "GPT-4o",
  "api_key": "sk-...",
  "base_url": null,
  "model_selected": "gpt-4o",
  "priority": 1
}
```

### `DELETE /api/v1/settings/providers/{provider_id}`
Delete an AI provider.

### `POST /api/v1/settings/providers/{provider_id}/validate`
Validate an AI provider connection. Tests API key and measures latency.

### `PATCH /api/v1/settings/providers/{provider_id}`
Update provider settings (display name, priority, model, API key).

### `GET /api/v1/settings/system`
List all system settings.

### `PATCH /api/v1/settings/system/{setting_id}`
Update a system setting.

---

## Identity Check (`app/routers/identcheck.py`)

### `POST /api/v1/candidates/{candidate_id}/identcheck/upload`
Upload identity document (front + optional back image).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `front_image` | File | Yes | Front of ID card |
| `back_image` | File | No | Back of ID card |
| `document_type` | string | Yes | e.g., "passport", "id_card" |

### `GET /api/v1/candidates/{candidate_id}/identcheck`
Get identity check status for a candidate.

### `POST /api/v1/identcheck/{document_id}/verify`
Verify identity document data manually (recruiter confirms extracted data).

**Body:**
```json
{
  "surname": "Mustermann",
  "given_names": "Max",
  "date_of_birth": "1990-01-15",
  "place_of_birth": "Berlin",
  "nationality": "German",
  "document_number": "XYZ123456"
}
```
