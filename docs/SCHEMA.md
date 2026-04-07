# Extraction JSON Schema

This document describes the JSON structure returned by the AI extraction and consumed by the template population service.

---

## Root Object

```json
{
  "candidate": { ... },
  "job_posting": { ... },
  "employment_history": [ ... ],
  "education": { ... },
  "technical_skills": [ ... ],
  "language_skills": [ ... ]
}
```

---

## `candidate`

Personal information extracted from the CV.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `full_name` | string | Full name of the candidate | `"Dariusz Jan Paluch"` |
| `nationality` | string | Nationality | `"Polish"` |
| `date_of_birth` | string | Date of birth (ISO 8601) | `"1985-03-15"` |
| `position` | string | Target position / job title | `"Schweißer (MIG/MAG)"` |

---

## `job_posting`

Job posting details. Some fields left blank for the recruiter to fill in.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Job title | `"Schweißer (MIG/MAG)"` |
| `ekp` | string | Entgeltgruppenposition (EKP) | `""` |
| `svs` | string | Sozialversicherung | `""` |
| `start_date` | string | Desired start date | `"01.04.2026"` |

**Note:** `ekp` and `svs` are typically filled by the recruiter, not extracted from the CV.

---

## `employment_history`

Array of employment records, sorted chronologically (oldest to newest).

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `start_date` | string | Start date (MM.YYYY) | `"01.2020"` |
| `end_date` | string | End date (MM.YYYY) or `"heute"` | `"heute"` |
| `employer` | string | Company name + city/country | `"Stahlbau GmbH, Berlin"` |
| `position` | string | Job title | `"Schweißer"` |
| `duties` | string[] | List of duties/activities | `["MAG Schweißen (135) ..."]` |

**Duties detail:** Should include welding process numbers (111, 135, 136, 138, 141), materials, component types, and sheet/wall thicknesses.

**Gap handling:** Timeline gaps are filled with synthetic records:
- `"Zeitpuffer/Projektpause"` — project break
- `"Weiterbildung"` — training/education period

---

## `education`

### `higher_education`

Array of formal education records (school, vocational training).

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `years` | string | Period attended | `"2005 - 2009"` |
| `institution` | string | School/institution name | `"Technikum Mechaniczne"` |
| `field` | string | Field of study | `"Metallverarbeitung"` |

### `further_training`

Array of additional training/certification records.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `years` | string | Year completed | `"2016"` |
| `institution` | string | Certifying body | `"TÜV Akademie"` |
| `field` | string | Certification topic | `"Schweißerzusatzqualifikation MAG (135)"` |

---

## `technical_skills`

Array of technical skills with proficiency levels.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Skill name (German) | `"MAG Schweißen"` |
| `level` | string | Proficiency level | `"Expert"` |

### Level Assessment Logic

| Level | Years of Experience | Independence | Project Complexity |
|-------|-------------------|--------------|--------------------|
| **Expert** | 8-10+ years | Fully independent | Demanding/complex projects |
| **Advanced** | 3-8 years | Independent | Regular projects |
| **Intermediate** | 1-3 years | Under supervision | Simple projects |
| **Basic** | < 1 year | Guided only | Basic tasks |

### Standard Skills Evaluated

- Handwerkliches Geschick (Manual dexterity)
- Installation
- Demontage
- Blechbearbeitung (Sheet metal working)
- Montieren von Stahlkonstruktionen (Steel structure assembly)
- Sägen / Schleifen / Schrauben (Sawing/Grinding/Screwing)
- Bohren (Drilling)
- Schweißarbeiten frei Hand (Manual welding)
- Schweißarbeiten mit Schweißroboter (Robotic welding)
- MAG Schweißen
- WIG Schweißen

---

## `language_skills`

Array of language proficiencies.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `language` | string | Language name (German) | `"Deutsch"` |
| `level` | string | Proficiency level | `"B1"` |

### Level Values

- CEFR levels: `A1`, `A2`, `B1`, `B2`, `C1`, `C2`
- Descriptive: `Muttersprache`, `kommunikativ` (maps to B1-B2), `Fließend`

---

## Database Storage Mapping

The extraction JSON maps to database models as follows:

| JSON Field | Database Model | Notes |
|-----------|---------------|-------|
| `candidate` | `Candidate` | `full_name`, `date_of_birth`, `nationality` |
| `employment_history` | `EmploymentRecord` | `company_name`, `job_title`, `start_date`, `end_date`, `description` (duties) |
| `education.higher_education` | `EducationRecord` | `degree_type="higher"`, `institution`, `field_of_study`, `graduation_year` |
| `education.further_training` | `EducationRecord` | `degree_type="further"`, `institution`, `field_of_study` |
| `technical_skills` | `SkillRecord` | `skill_name`, `level`, `category="technical"` |
| `language_skills` | `LanguageRecord` | `language`, `level_raw`, `level_normalized` |
