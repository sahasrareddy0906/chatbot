from database.client import supabase
from datetime import datetime, timezone


VIOLATION_WARNING    = 3   # show warning after this many
VIOLATION_SUSPICIOUS = 5   # flag as suspicious after this many


def log_proctoring_event(session_id: str,
                          candidate_id: str,
                          event_type: str) -> dict | None:
    """
    Log a single proctoring event.
    event_type: "present" | "face_absent" | "multiple_faces"
    Only violations (not present events) increment count.
    """
    is_violation = event_type in [
        "face_absent", "multiple_faces"
    ]

    # Insert event log
    log_resp = (
        supabase.table("proctoring_log")
        .insert({
            "session_id":   session_id,
            "candidate_id": candidate_id,
            "event_type":   event_type,
            "created_at":   datetime.now(timezone.utc).isoformat()
        })
        .execute()
    )

    if not is_violation:
        return {"logged": True, "violation": False}

    # Increment violation count on session
    session_resp = (
        supabase.table("exam_session")
        .select("violation_count, proctoring_status")
        .eq("id", session_id)
        .execute()
    )

    if not session_resp.data:
        return None

    session        = session_resp.data[0]
    new_count      = (session.get("violation_count") or 0) + 1
    new_status     = session.get("proctoring_status", "active")

    # Update status based on violation count
    if new_count >= VIOLATION_SUSPICIOUS:
        new_status = "suspicious"
    elif new_count >= VIOLATION_WARNING:
        new_status = "warning"

    update_resp = (
        supabase.table("exam_session")
        .update({
            "violation_count":   new_count,
            "proctoring_status": new_status
        })
        .eq("id", session_id)
        .execute()
    )

    return {
        "logged":            True,
        "violation":         True,
        "violation_count":   new_count,
        "proctoring_status": new_status,
        "show_warning":      new_count == VIOLATION_WARNING,
        "is_suspicious":     new_count >= VIOLATION_SUSPICIOUS
    }


def get_proctoring_summary(session_id: str) -> dict:
    """
    Returns full proctoring summary for a session.
    Used by HR dashboard to review candidate behaviour.
    """
    # Get session violation data
    session_resp = (
        supabase.table("exam_session")
        .select("violation_count, proctoring_status")
        .eq("id", session_id)
        .execute()
    )

    session = session_resp.data[0] if session_resp.data else {}

    # Get all violation logs
    logs_resp = (
        supabase.table("proctoring_log")
        .select("event_type, created_at")
        .eq("session_id", session_id)
        .neq("event_type", "present")
        .order("created_at")
        .execute()
    )

    logs = logs_resp.data if logs_resp.data else []

    # Count by type
    face_absent_count    = sum(
        1 for l in logs if l["event_type"] == "face_absent"
    )
    multiple_faces_count = sum(
        1 for l in logs if l["event_type"] == "multiple_faces"
    )

    return {
        "proctoring_status":    session.get(
            "proctoring_status", "active"
        ),
        "total_violations":     session.get("violation_count", 0),
        "face_absent_count":    face_absent_count,
        "multiple_faces_count": multiple_faces_count,
        "violation_log":        logs
    }


def finalise_proctoring(session_id: str) -> None:
    """
    Called when exam is submitted.
    Sets final proctoring status —
    if no violations mark as "clean".
    """
    session_resp = (
        supabase.table("exam_session")
        .select("violation_count, proctoring_status")
        .eq("id", session_id)
        .execute()
    )

    if not session_resp.data:
        return

    session = session_resp.data[0]
    count   = session.get("violation_count", 0)

    if count == 0:
        final_status = "clean"
    elif count < VIOLATION_WARNING:
        final_status = "clean"     # minor, still clean
    elif count < VIOLATION_SUSPICIOUS:
        final_status = "warning"
    else:
        final_status = "suspicious"

    supabase.table("exam_session").update(
        {"proctoring_status": final_status}
    ).eq("id", session_id).execute()