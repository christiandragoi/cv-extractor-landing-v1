# CV Extractor

AI-powered CV extraction pipeline that converts candidate resumes (PDF, DOCX, JPEG) into structured German recruitment documents (Lebenslauf) using Word templates.

## Features

- **Multi-format CV parsing** — PDF, DOCX, JPEG (via OCR/Vision)
- **AI-powered extraction** — Structured data extraction using configurable AI providers
- **Template population** — Fills Word templates with extracted data automatically
- **Multi-provider failover** — OpenAI, OpenRouter, DeepSeek, xAI, Groq, and more
- **Recruiter review workflow** — Review, edit, and approve extracted data
- **Identity verification** — Upload and verify identity documents
- **Encrypted secrets** — API keys encrypted at rest with Fernet

## Quick Start

### Prerequisites
- Python 3.11+
- An AI provider API key (OpenAI, etc.)

### Run locally

```bash
# Clone the repo
git clone <repo-url> && cd cv-extractor-phase1

# Create virtual environment and install deps
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.local.txt

# Set up environment
cp .env.example .env
# Edit .env - at minimum set ENCRYPTION_KEY and an AI provider key

# Run
python run_local.py
```

The API starts at **http://localhost:8001**  
Swagger docs: **http://localhost:8001/docs**

### Run with Docker

```bash
docker-compose up --build
```

## Project Structure

```
cv-extractor-phase1/
├── app/
│   ├── ai/                    # AI provider abstraction
│   │   ├── base_provider.py   # Abstract base provider
│   │   ├── circuit_breaker.py # Failover circuit breaker
│   │   ├── openai_provider.py # OpenAI-compatible provider
│   │   └── provider_manager.py# Multi-provider management
│   ├── domain/                # Domain logic
│   │   └── normalization/     # GDPR, timeline normalization
│   ├── models/                # SQLAlchemy ORM models
│   ├── routers/               # FastAPI route handlers
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic
│   │   ├── candidate_service.py
│   │   ├── extraction_service.py
│   │   └── template_population_service.py  # Master prompt + template filling
│   ├── storage/               # File storage abstraction
│   ├── resources/templates/   # Word template files
│   ├── config.py              # Settings (env-based)
│   ├── database.py            # Async SQLAlchemy setup
│   ├── db_types.py            # PG/SQLite type compatibility
│   └── main.py                # FastAPI app entry point
├── docs/
│   ├── ARCHITECTURE.md        # System architecture & pipeline
│   ├── API.md                 # Full API reference
│   ├── DATABASE.md            # Database model documentation
│   ├── PROMPTS.md             # AI prompt documentation
│   └── SCHEMA.md              # Extraction JSON schema
├── examples/
│   ├── sample_cv_paluch.jpeg  # Sample CV for testing
│   ├── expected_output.json   # Expected extraction output
│   └── sample_output_lebenslauf.docx  # Sample populated document
├── static/                    # Frontend (single-page HTML)
├── migrations/                # Alembic migrations
├── tests/                     # Test suite
├── .env.example               # Environment template
├── Dockerfile                 # Container build
├── docker-compose.yml         # Container orchestration
├── requirements.txt           # Full dependency list
├── requirements.local.txt     # Core dependencies (local dev)
└── run_local.py               # Local dev launcher
```

## The Extraction Pipeline

```
1. Upload CV (PDF/DOCX/JPEG)
       ↓
2. Text Extraction (pdfplumber / python-docx / AI Vision)
       ↓
3. AI Structured Extraction (WELDER_MASTER_PROMPT → JSON)
       ↓
4. Store in Database (Candidate + Employment + Skills + Languages)
       ↓
5. [Optional] Recruiter Review & Edit
       ↓
6. Template Population (Word .docx with 6 tables)
       ↓
7. Download Populated Lebenslauf
```

### How Template Population Works

The Word template contains 6 tables populated by `TemplatePopulationService`:

| Table | Content | Source Field |
|-------|---------|-------------|
| Table 0 | Job header (EKP, SVS, Starttermin, Title) | `job_posting` |
| Table 1 | Berufserfahrung (Employment history) | `employment_history[]` |
| Table 2 | Bildungseinrichtung (Higher education) | `education.higher_education[]` |
| Table 3 | Weiterbildung (Further training) | `education.further_training[]` |
| Table 4 | Fähigkeiten (Technical skills with levels) | `technical_skills[]` |
| Table 5 | Sprachkenntnisse (Languages) | `language_skills[]` |

## Adding New Templates

1. Create a Word document (.docx) with 6 tables matching the schema above
2. Use Jinja2-style placeholders if desired (they get cleaned automatically)
3. Upload via API: `POST /api/v1/templates/upload`
4. Or manually place in `app/resources/templates/`

## Customizing Prompts

The master extraction prompt is in `app/services/template_population_service.py` as `WELDER_MASTER_PROMPT`.

To add a prompt for a different job type:
1. Create a new prompt constant (e.g., `ELECTRICIAN_MASTER_PROMPT`)
2. Update `ExtractionService` to select prompts based on job profile
3. Follow the same JSON output schema

## AI Provider Setup

Providers are configured via the API (stored in the database):

```bash
# Create a provider
curl -X POST http://localhost:8001/api/v1/settings/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "OPENAI",
    "display_name": "GPT-4o",
    "api_key": "sk-your-key",
    "model_selected": "gpt-4o",
    "priority": 1
  }'

# Validate connection
curl -X POST http://localhost:8001/api/v1/settings/providers/<id>/validate
```

Supported providers: OPENAI, OPENROUTER, TOGETHER, XAI, DEEPSEEK, MINIMAX, KIMI, QWEN, GROQ

## Environment Variables

See [.env.example](.env.example) for all configuration options.

Key variables:
- `DATABASE_URL` — SQLite for local, PostgreSQL for production
- `ENCRYPTION_KEY` — Required for encrypting API keys (generate with Fernet)
- `OPENAI_API_KEY` — Fallback AI key (DB providers preferred)
- `CORS_ORIGINS` — Comma-separated allowed origins

## License

Internal use — Arbeitsvermittlung / Personnel Services.
