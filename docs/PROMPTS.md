# AI Prompts Documentation

## Master Extraction Prompt: `WELDER_MASTER_PROMPT`

**Location:** `app/services/template_population_service.py`

This is the core prompt used by the AI to extract structured data from welder (Schweißer) CVs. It is sent as the **system message** to the AI provider.

---

### Prompt (Original German)

The prompt instructs the AI to act as a **professional German recruiting assistant for welder candidates** (`professioneller deutscher Recruiting-Assistent für Schweißerkandidaten`).

### Extraction Rules

The prompt defines 6 extraction categories with specific rules:

#### 1. BERUFSERFAHRUNG (Employment History)
- **Format:** `MM.JJJJ – MM.JJJJ` (left column), details (right column)
- **Sorting:** From age 19 onwards, gapless until today
- **Gap filling:** Gaps filled with "Zeitpuffer/Projektpause" or "Weiterbildung"
- **Per position:** Employer + City/Country, Position, Duties
- **Duty detail:** Welding processes (111, 135, 136, 138, 141), materials, typical components, sheet/wall thicknesses

#### 2. BILDUNGSEINRICHTUNG (Higher Education)
- Extract school/vocational training from CV
- If missing: realistic school near birthplace
- Age 15-18, preference for metalworking-related education

#### 3. WEITERBILDUNG (Further Training)
- All welding courses and certifications (111, 135, 136, 138, 141)
- Include period and type (basic/advanced course)

#### 4. SPRACHKENNTNISSE (Language Skills)
- Tabular format: Language + Level (C2, B1, A2, "kommunikativ")
- "communicative" maps to B1-B2

#### 5. TECHNISCHE FÄHIGKEITEN (Technical Skills) — CRITICAL
Evaluation logic based on experience:

| Level | Criteria |
|-------|----------|
| **Expert** | 8-10+ years regular use, demanding projects |
| **Advanced** | 3-8 years, regularly applied, independent |
| **Intermediate** | 1-3 years, supervised or simple projects |
| **Basic** | Basic knowledge only, short deployments |

**Skills to evaluate:**
- Handwerkliches Geschick (Manual dexterity)
- Installation, Demontage
- Blechbearbeitung (Sheet metal working)
- Montieren von Stahlkonstruktionen (Steel structure assembly)
- Sägen / Schleifen / Schrauben (Sawing/Grinding/Screwing)
- Bohren (Drilling)
- Schweißarbeiten frei Hand (Manual welding)
- Schweißarbeiten mit Schweißroboter (Robotic welding)
- MAG Schweißen, WIG Schweißen

#### 6. DATENSCHUTZ (Data Privacy)
- Remove private contact details (phone, email, address)
- Use placeholders for Verleiher/Personaldienstleister (agencies)

### Output Format

The AI must respond with **JSON only** — no markdown, no explanations:

```json
{
  "candidate": {"full_name": "...", "nationality": "...", "date_of_birth": "YYYY-MM-DD", "position": "..."},
  "job_posting": {"title": "Schweißer (MIG/MAG)", "ekp": "", "svs": "", "start_date": ""},
  "employment_history": [
    {"start_date": "MM.JJJJ", "end_date": "MM.JJJJ", "employer": "...", "position": "...", "duties": ["..."]}
  ],
  "education": {
    "higher_education": [{"years": "YYYY - YYYY", "institution": "...", "field": "..."}],
    "further_training": [{"years": "YYYY", "institution": "...", "field": "..."}]
  },
  "technical_skills": [{"name": "MAG Schweißen", "level": "Expert"}],
  "language_skills": [{"language": "Deutsch", "level": "B1"}]
}
```

---

## Custom Instructions

Additional instructions can be appended via the `instructions` parameter when calling the extraction endpoint. These are added to the system prompt as:

```
ZUSÄTZLICHE ANWEISUNGEN DES OPERATORS:
<your custom instructions>
```

## Modifying the Prompt

To customize extraction behavior:

1. Edit `WELDER_MASTER_PROMPT` in `app/services/template_population_service.py`
2. For different job profiles (non-welder), create a new prompt constant
3. Update `ExtractionService` to select the appropriate prompt based on job profile type
