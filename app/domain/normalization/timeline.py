from datetime import date, timedelta, datetime
from typing import List
from uuid import uuid4


def detect_gaps(employment_history: List[dict]) -> List[dict]:
    if not employment_history:
        return []

    def parse_date(d):
        if not d:
            return None
        if isinstance(d, date):
            return d
        try:
            return datetime.strptime(d, '%Y-%m-%d').date()
        except Exception:
            return None

    sorted_jobs = sorted(
        [j for j in employment_history if parse_date(j.get('start_date'))],
        key=lambda x: parse_date(x['start_date']),
        reverse=True
    )
    gaps = []

    for i in range(len(sorted_jobs) - 1):
        current_job = sorted_jobs[i]
        next_job = sorted_jobs[i + 1]

        current_end = parse_date(current_job.get('end_date')) or date.today()
        next_start = parse_date(next_job['start_date'])

        if not next_start:
            continue

        gap_days = (next_start - current_end).days
        if gap_days > 31:
            gaps.append({
                'id': str(uuid4()),
                'is_gap_record': True,
                'start_date': (current_end + timedelta(days=1)).isoformat(),
                'end_date': (next_start - timedelta(days=1)).isoformat(),
                'company_name': "ZEITLÜCKE" if gap_days > 180 else "Unterbrechung",
                'job_title': "Erklärung erforderlich",
                'gap_type': "UNKNOWN",
                'gap_note': f"Lücke von {gap_days} Tagen",
                'description': [],
                'inferred': True,
                'needs_review': True
            })

    return gaps
