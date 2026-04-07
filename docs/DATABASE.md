# Database Models Documentation

## Overview

The application uses **SQLAlchemy 2.0** with async sessions. Models are defined in `app/models/` and registered in `app/models/__init__.py` (which must be imported before `Base.metadata.create_all`).

### Type Compatibility Layer (`app/db_types.py`)

The app abstracts PostgreSQL vs SQLite differences:
- **PostgreSQL:** Uses native `UUID` and `JSONB` types
- **SQLite:** Uses `CHAR(36)` for UUIDs and `JSON` for JSONB

Auto-detected from `DATABASE_URL` prefix.

---

## Models

### Candidate (`app/models/candidate.py`)
**Table:** `candidates`

The core entity. Tracks a candidate through the extraction pipeline.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `created_at` | DateTime(tz) | Creation timestamp |
| `updated_at` | DateTime(tz) | Last update timestamp |
| `status` | String(50) | Pipeline status (default: `"UPLOADED"`) |
| `original_filename` | String(255) | Uploaded CV filename |
| `original_file_path` | String(500) | Storage path to original CV |
| `structured_cv_path` | String(500)? | Path to populated DOCX |
| `final_cv_path` | String(500)? | Path to final CV (Stage 2) |
| `job_profile_id` | UUID? (FK) | Reference to `job_profiles.id` |
| `recruiter_notes` | Text? | Notes from recruiter |
| `extraction_provider` | String(100)? | AI provider used for extraction |
| `extraction_model` | String(100)? | AI model used |
| `extraction_duration_ms` | int? | Extraction time in milliseconds |
| `error_log` | JSONB? | Error details on failure |
| `approval_timestamp` | DateTime(tz)? | When candidate was approved |
| `approved_by` | String(100)? | Who approved |
| `full_name` | String(255)? | Extracted full name |
| `date_of_birth` | Date? | Extracted DOB |
| `nationality` | String(100)? | Extracted nationality |
| `needs_review` | Boolean | Whether data needs review (default: `true`) |

**Status values:** `UPLOADED` → `EXTRACTING` → `EXTRACTED` → `PENDING_REVIEW` → `APPROVED` → `GENERATING_STAGE2` → `COMPLETED` / `FAILED`

**Relationships:**
- `employment_history` → `EmploymentRecord[]` (cascade delete)
- `education_records` → `EducationRecord[]` (cascade delete)
- `language_records` → `LanguageRecord[]` (cascade delete)
- `skill_records` → `SkillRecord[]` (cascade delete)
- `identity_documents` → `IdentityDocument[]` (cascade delete)
- `audit_logs` → `AuditLog[]` (cascade delete)

---

### EmploymentRecord (`app/models/employment.py`)
**Table:** `employment_records`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `sort_order` | int | Display order (default: 0) |
| `company_name` | String(255) | Employer name |
| `job_title` | String(255) | Position title |
| `job_title_original` | String(255)? | Original title from CV |
| `start_date` | Date? | Employment start |
| `end_date` | Date? | Employment end |
| `is_current` | Boolean | Currently employed here |
| `location` | String(255)? | Job location |
| `description` | JSONB (str[]) | List of duties |
| `is_gap_record` | Boolean | Synthetic gap-filling record |
| `gap_type` | String(50)? | Type: "career_break", "education", etc. |
| `gap_note` | String(500)? | Note about the gap |
| `technologies` | JSONB (str[]) | Technologies/skills used |
| `inferred` | Boolean | Was this AI-inferred? |
| `needs_review` | Boolean | Needs recruiter review |

---

### EducationRecord (`app/models/education.py`)
**Table:** `education_records`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `sort_order` | int | Display order |
| `institution` | String(255) | School/institution name |
| `degree_type` | String(50) | "higher" or "further" |
| `field_of_study` | String(255)? | Field/major |
| `graduation_year` | int? | Year of graduation |
| `is_completed` | Boolean | Degree completed (default: `true`) |
| `notes` | Text? | Additional notes |
| `inferred` | Boolean | AI-inferred |
| `needs_review` | Boolean | Needs review |

---

### SkillRecord (`app/models/skill.py`)
**Table:** `skill_records`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `skill_name` | String(255) | Skill name |
| `category` | String(50) | Skill category (e.g., "technical") |
| `level` | String(50) | Proficiency level |
| `years_of_experience` | float? | Estimated years |
| `evidence` | Text? | Evidence/justification |
| `is_verified` | Boolean | Verified by recruiter |
| `inferred` | Boolean | AI-inferred (default: `true`) |
| `needs_review` | Boolean | Needs review (default: `true`) |

---

### LanguageRecord (`app/models/language.py`)
**Table:** `language_records`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `language` | String(100) | Language name |
| `level_raw` | String(100)? | Original level from CV |
| `level_normalized` | String(50) | Normalized CEFR level |
| `evidence` | String(255)? | Evidence for the level |
| `inferred` | Boolean | AI-inferred (default: `true`) |
| `needs_review` | Boolean | Needs review (default: `true`) |

---

### AIProvider (`app/models/ai_provider.py`)
**Table:** `ai_providers`

Stores AI provider configurations with encrypted API keys.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `provider_type` | String(50) | e.g., "OPENAI", "OPENROUTER", "DEEPSEEK" |
| `display_name` | String(100) | Human-readable name |
| `api_key_encrypted` | bytes | Fernet-encrypted API key |
| `api_key_hint` | String(10) | Last 4 chars for identification |
| `base_url` | String(255)? | Custom API endpoint |
| `model_selected` | String(100) | Active model name |
| `models_available` | JSONB (str[]) | List of available models |
| `is_active` | Boolean | Active for use (default: `true`) |
| `is_validated` | Boolean | Connection tested |
| `validation_last_attempt` | DateTime(tz)? | Last validation timestamp |
| `validation_latency_ms` | int? | Validation response time |
| `priority` | int | Failover priority (default: `1`, lower = higher) |
| `circuit_breaker_failures` | int | Consecutive failures |
| `circuit_breaker_last_failure` | DateTime(tz)? | Last failure timestamp |
| `circuit_breaker_state` | String(20) | "CLOSED", "OPEN", "HALF_OPEN" |
| `rate_limit_rpm` | int | Requests per minute limit (default: `60`) |
| `created_at` | DateTime(tz) | Creation timestamp |

**Supported provider types:** OPENAI, OPENROUTER, TOGETHER, XAI, DEEPSEEK, MINIMAX, KIMI, QWEN, GROQ

---

### Template (`app/models/template.py`)
**Table:** `templates`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | String(255) | Template display name |
| `template_type` | String(50) | "lebenslauf", "anschreiben", "zeugnis" |
| `file_path` | String(512) | Path to .docx file |
| `file_size` | String(20) | Human-readable size |
| `is_active` | Boolean | Currently active template |
| `fields` | JSONB (str[]) | List of template fields |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update |

---

### SystemSetting (`app/models/system_setting.py`)
**Table:** `system_settings`

Stores encrypted system configuration values.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `category` | String(50) | Setting category |
| `key_name` | String(100) | Unique key identifier |
| `value_encrypted` | bytes | Fernet-encrypted value |
| `value_hint` | String(50)? | Hint for display |
| `is_active` | Boolean | Active setting |
| `description` | String(255)? | Description |
| `created_at` | DateTime(tz) | Creation timestamp |
| `updated_at` | DateTime(tz) | Last update |

---

### IdentityDocument (`app/models/identity_document.py`)
**Table:** `identity_documents`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `created_at` | DateTime(tz) | Upload timestamp |
| `document_type` | String(50) | "passport", "id_card", etc. |
| `file_path_front` | String(500)? | Front image path |
| `file_path_back` | String(500)? | Back image path |
| `generated_docx_path` | String(500)? | Generated verification document |
| `surname` | String(255)? | Extracted surname |
| `given_names` | String(255)? | Extracted given names |
| `date_of_birth` | Date? | Extracted DOB |
| `place_of_birth` | String(255)? | Extracted birthplace |
| `nationality` | String(100)? | Extracted nationality |
| `document_number` | String(100)? | Document number |
| `issue_date` | Date? | Issue date |
| `expiry_date` | Date? | Expiry date |
| `confidence_scores` | JSONB | OCR confidence per field |
| `requires_manual_review` | Boolean | Needs manual verification |
| `recruiter_verified` | Boolean | Verified by recruiter |
| `status` | String(50) | "UPLOADED", "VERIFIED", "EXPORTED" |

---

### AuditLog (`app/models/audit_log.py`)
**Table:** `audit_logs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `candidate_id` | UUID (FK) | Reference to `candidates.id` (CASCADE) |
| `timestamp` | DateTime(tz) | Event timestamp |
| `action` | String(100) | Action type (e.g., "IDENTCHECK_UPLOAD") |
| `user_id` | String(255)? | User who performed action |
| `details` | JSONB? | Additional context |

---

### JobProfile (`app/models/job_profile.py`)
**Table:** `job_profiles`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | String(100) | Profile name (unique) |
| `category` | String(50) | Job category |
| `extraction_instructions` | Text? | Custom extraction instructions |
| `required_skills` | JSONB (str[]) | Required skill names |
| `gap_handling_rules` | JSONB | Rules for filling timeline gaps |
| `is_active` | Boolean | Active for use |
| `created_at` | DateTime(tz) | Creation timestamp |

---

## Entity Relationship Diagram (simplified)

```
Candidate ───┬── EmploymentRecord[]
             ├── EducationRecord[]
             ├── SkillRecord[]
             ├── LanguageRecord[]
             ├── IdentityDocument[]
             ├── AuditLog[]
             └── JobProfile (optional FK)

AIProvider (standalone)
Template (standalone)
SystemSetting (standalone)
```
