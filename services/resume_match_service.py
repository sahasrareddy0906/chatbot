from database.client import supabase
from datetime import datetime, timezone


def create_resume_record(candidate_id: str, drive_id: str,
                         storage_path: str,
                         filename: str) -> dict | None:
    """
    Create or update the resume_match row for a candidate.
    This is the record that will later hold extracted skills
    and match percentage once OpenAI processes it (Day 28-29).
    """
    # Check if a record already exists (re-upload case)
    existing = (
        supabase.table("resume_match")
        .select("id")
        .eq("candidate_id", candidate_id)
        .execute()
    )

    data = {
        "candidate_id":  candidate_id,
        "drive_id":      drive_id,
        "resume_url":    storage_path,  # storing path, not signed URL
        "extracted_skills": None,   # filled on Day 28
        "match_percentage": None,   # filled on Day 29
        "passed":        False,
        "ai_questions":  None,      # filled on Day 30
        "ai_answers":    None,      # filled on Day 30
        "created_at":    datetime.now(timezone.utc).isoformat()
    }

    if existing.data:
        response = (
            supabase.table("resume_match")
            .update(data)
            .eq("candidate_id", candidate_id)
            .execute()
        )
    else:
        response = (
            supabase.table("resume_match")
            .insert(data)
            .execute()
        )

    return response.data[0] if response.data else None


def get_resume_by_candidate(candidate_id: str) -> dict | None:
    """Fetch resume record for one candidate."""
    response = (
        supabase.table("resume_match")
        .select("*")
        .eq("candidate_id", candidate_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_resumes_by_drive(drive_id: str) -> list:
    """Fetch all resume records for a drive."""
    response = (
        supabase.table("resume_match")
        .select("*")
        .eq("drive_id", drive_id)
        .execute()
    )
    return response.data if response.data else []


def get_shortlisted_candidates_with_resume_status(
    drive_id: str
) -> list:
    """
    Returns shortlisted candidates with their resume upload status.
    This drives the resume upload page UI — shows who still
    needs a resume uploaded and who's done.
    """
    # Get shortlisted candidate_ids from exam_result
    results_resp = (
        supabase.table("exam_result")
        .select("candidate_id, total_score")
        .eq("hr_shortlisted", True)
        .execute()
    )

    if not results_resp.data:
        return []

    shortlisted_ids = [r["candidate_id"] for r in results_resp.data]
    scores_by_id    = {
        r["candidate_id"]: r["total_score"]
        for r in results_resp.data
    }

    # Get candidate details — filter to this drive only
    candidates_resp = (
        supabase.table("candidate")
        .select("id, email, username, experience_band")
        .eq("drive_id", drive_id)
        .in_("id", shortlisted_ids)
        .execute()
    )

    candidates = candidates_resp.data if candidates_resp.data else []

    # Get existing resume records
    resumes = get_resumes_by_drive(drive_id)
    resumes_by_candidate = {
        r["candidate_id"]: r for r in resumes
    }

    result = []
    for c in candidates:
        resume = resumes_by_candidate.get(c["id"])
        result.append({
            "candidate_id":     c["id"],
            "email":            c["email"],
            "username":         c["username"],
            "experience_band":  c["experience_band"],
            "total_score":      scores_by_id.get(c["id"]),
            "has_resume":       resume is not None,
            "resume_filename":  resume.get("resume_url", "").split("/")[-1]
                                if resume else None
        })

    # Sort by score descending
    result.sort(
        key=lambda x: -(x["total_score"] or 0)
    )

    return result