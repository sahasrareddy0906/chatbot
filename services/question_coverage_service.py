from services.question_service import (
    count_questions
)


ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data Engineer",
    "Data Scientist",
    "DevOps Engineer",
    "Database Administrator",
    "QA Engineer",
    "Business Analyst",
    "HR Technology Specialist"
]


EXPERIENCE_BAND_SEGMENTS = {
    "0-2": ["technical", "analytical"],
    "2-5": ["technical", "analytical", "domain"],
    "5+": ["technical", "analytical", "domain", "management"]
}


REQUIRED_MINIMUM = 30


def get_question_coverage():
    """
    Query question table and return coverage statistics.
    
    Returns list of dicts with:
    - role
    - segment
    - experience_band
    - count
    """
    coverage = []

    for role in ROLES:
        for band, segments in EXPERIENCE_BAND_SEGMENTS.items():
            for segment in segments:
                count = count_questions(role, segment, band)

                coverage.append({
                    "role": role,
                    "segment": segment,
                    "experience_band": band,
                    "count": count
                })

    return coverage


def find_missing_combinations():
    """
    Identify combinations with fewer than REQUIRED_MINIMUM questions.
    
    Returns list of dicts with:
    - role
    - segment
    - experience_band
    - existing (current count)
    - required (minimum threshold)
    - missing (required - existing)
    """
    coverage = get_question_coverage()
    missing = []

    for item in coverage:
        existing = item["count"]

        if existing < REQUIRED_MINIMUM:
            gap = {
                "role": item["role"],
                "segment": item["segment"],
                "experience_band": item["experience_band"],
                "existing": existing,
                "required": REQUIRED_MINIMUM,
                "missing": REQUIRED_MINIMUM - existing
            }
            missing.append(gap)

    return missing


def get_coverage_summary():
    """
    Return aggregated coverage statistics.
    
    Returns dict with:
    - total_roles
    - total_combinations
    - complete_combinations
    - incomplete_combinations
    - total_questions
    """
    coverage = get_question_coverage()

    total_combinations = len(coverage)
    complete_combinations = sum(
        1 for item in coverage if item["count"] >= REQUIRED_MINIMUM
    )
    incomplete_combinations = total_combinations - complete_combinations
    total_questions = sum(item["count"] for item in coverage)

    return {
        "total_roles": len(ROLES),
        "total_combinations": total_combinations,
        "complete_combinations": complete_combinations,
        "incomplete_combinations": incomplete_combinations,
        "total_questions": total_questions
    }
