# CV Extractor - Phase 1 Implementation

FastAPI backend for German CV extraction and processing.

## Quick Start

```bash
# 1. Copy env and add your keys
cp .env.example .env

# 2. Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste output as ENCRYPTION_KEY in .env

# 3. Start all services
docker-compose up --build

# 4. Access
# API:   http://localhost:8000
# Docs:  http://localhost:8000/docs
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16
- **Queue**: Redis + Celery
- **Storage**: Local filesystem (abstracted for S3)
- **AI**: Multi-provider with circuit breaker + fallback chain

## Status Workflow

```
UPLOADED → EXTRACTING → EXTRACTED → (review) → APPROVED → COMPLETED
```

## Key Features

1. **File Upload** — PDF/DOCX with UUID-based storage
2. **AI Extraction** — Async via Celery, multi-provider fallback
3. **GDPR Stripping** — Addresses/phones/emails removed before AI
4. **Gap Detection** — Auto-detects >31 day employment gaps, flags for review
5. **Human-in-the-Loop** — All AI data marked `needs_review=true`
6. **IdentCheck** — ID document upload and verification scaffold
7. **Encrypted Keys** — Provider API keys encrypted at rest via Fernet

## Critical Rules

- All AI-extracted data: `needs_review=true` by default
- Employment gaps >31 days: auto-detected and flagged
- Stage 2 generation blocked until `status=APPROVED`
- IdentCheck requires manual recruiter verification before export
