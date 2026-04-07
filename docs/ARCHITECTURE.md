# Architecture Overview

## System Purpose

CV Extractor automates the conversion of candidate CVs (PDF, DOCX, images) into structured German recruitment documents (Lebenslauf) using AI-powered data extraction and Word template population.

## Extraction Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Upload CV  │ ──▶ │ Extract Text │ ──▶ │ AI Extraction │ ──▶ │ Template Populate│ ──▶ │ Download DOCX│
│  (PDF/DOCX/ │     │  (pdfplumber │     │  (Master      │     │  (python-docx    │     │              │
│   JPEG)     │     │   / docx /   │     │   Prompt +    │     │   Jinja2-style   │     │              │
│             │     │   vision)    │     │   ProviderMgr)│     │   template)      │     │              │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────────┘     └──────────────┘
```

### Stage-by-Stage Breakdown

1. **Upload CV** — Candidate uploads a CV file (PDF, DOCX, DOC, JPEG). Optionally, recruiter adds notes and assigns a job profile.

2. **Extract Text** — Text is extracted using:
   - `pdfplumber` for PDFs
   - `python-docx` for DOCX files
   - AI Vision (GPT-4o) for JPEG images (base64-encoded)

3. **AI Extraction** — The extracted text is sent to an AI provider using the `WELDER_MASTER_PROMPT`. The system uses a `ProviderManager` with circuit-breaker pattern to try multiple AI providers in priority order. Returns structured JSON.

4. **Review (Optional)** — Extracted data is stored in the database. A recruiter can review/edit employment history, skills, languages before approval.

5. **Template Population** — A Word template (.docx) is populated with the structured data. The template uses 6 tables: job posting header, employment history, higher education, further training, technical skills, and languages.

6. **Download** — The populated DOCX is available for download.

## Frontend Wizard Flow

The frontend (single-page HTML at `static/index.html`) implements a step-by-step wizard:

1. **Upload** — Select and upload a CV file + choose a Word template
2. **Extraction** — AI processes the CV; progress bar shows extraction status
3. **Review** — Display extracted data in editable form; recruiter can correct entries
4. **Download** — Generate and download the populated Lebenslauf document

## Backend Architecture

### Framework
- **FastAPI** with async SQLAlchemy 2.0
- SQLite (local dev) / PostgreSQL (production) with transparent type switching via `app/db_types.py`

### AI Provider System
- Pluggable multi-provider support (OpenAI, OpenRouter, Together, xAI, DeepSeek, Kimi, Qwen, Groq, MiniMax)
- All providers use OpenAI-compatible API format
- API keys encrypted at rest (Fernet via `cryptography`)
- Circuit breaker pattern for failover
- Providers configured via API (stored in database, not .env)

### Storage
- Local filesystem storage (`LocalStorage`) with directory traversal protection
- Configurable root path via `STORAGE_ROOT`

### Router Organization

| Router | Prefix | Purpose |
|--------|--------|---------|
| `candidates.py` | `/api/v1` | CV upload, list, get, delete |
| `processing.py` | `/api/v1` | Trigger extraction, poll status |
| `review.py` | `/api/v1` | Review extracted data, approve candidate |
| `extraction.py` | `/api/v1/extraction` | End-to-end: upload template+CV → AI extract → populate → download |
| `templates.py` | `/api/v1/templates` | Template CRUD (upload, list, activate, delete) |
| `downloads.py` | `/api/v1` | Download structured/final CVs, identity document export |
| `settings_router.py` | `/api/v1/settings` | AI provider management, system settings |
| `identcheck.py` | `/api/v1` | Identity document upload, verification workflow |

### Key Services

| Service | File | Purpose |
|---------|------|---------|
| `CandidateService` | `services/candidate_service.py` | Candidate CRUD, file storage |
| `ExtractionService` | `services/extraction_service.py` | AI extraction orchestration |
| `TemplatePopulationService` | `services/template_population_service.py` | Word template population |
| `ProviderManager` | `ai/provider_manager.py` | Multi-provider AI calls with failover |

### Database Models

- **Candidate** — Core record with status workflow (UPLOADED → EXTRACTING → EXTRACTED → PENDING_REVIEW → APPROVED → COMPLETED)
- **EmploymentRecord** — Job history entries (with gap detection)
- **EducationRecord** — Education and training
- **SkillRecord** — Technical skills with levels
- **LanguageRecord** — Language proficiencies
- **AIProvider** — Configured AI providers with encrypted keys
- **Template** — Word template metadata
- **SystemSetting** — Encrypted system configuration
- **IdentityDocument** — Identity verification documents
- **AuditLog** — Action audit trail
- **JobProfile** — Job posting templates with extraction rules
