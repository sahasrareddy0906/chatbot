from database.client import supabase
from datetime import datetime, timezone


def score_exam_session(session_id: str) -> dict | None:
    """
    Full scoring pipeline for a submitted exam session.
    1. Fetch all exam_question rows with question data
    2. Mark each as correct/incorrect
    3. Calculate segment scores
    4. Calculate total score
    5. Store in exam_result table
    6. Update candidate status
    """

    # Step 1 — fetch session
    session_resp = (
        supabase.table("exam_session")
        .select("*")
        .eq("id", session_id)
        .execute()
    )
    if not session_resp.data:
        return None

    session = session_resp.data[0]

    # Step 2 — fetch exam_question rows joined with question data
    eq_resp = (
        supabase.table("exam_question")
        .select("*, question(*)")
        .eq("session_id", session_id)
        .execute()
    )

    exam_questions = eq_resp.data if eq_resp.data else []

    if not exam_questions:
        return None

    # Step 3 — mark each answer correct/incorrect
    segment_results = {}  # { "technical": {"correct": 0, "total": 0}, ... }
    total_correct = 0
    total_questions = len(exam_questions)

    update_rows = []

    for eq in exam_questions:
        question        = eq["question"]
        segment         = question["segment"]
        candidate_ans   = eq.get("candidate_answer")
        correct_ans     = question["correct_answer"]

        is_correct = (
            candidate_ans is not None
            and candidate_ans.upper() == correct_ans.upper()
        )

        if is_correct:
            total_correct += 1

        # Track per segment
        if segment not in segment_results:
            segment_results[segment] = {"correct": 0, "total": 0}
        segment_results[segment]["total"] += 1
        if is_correct:
            segment_results[segment]["correct"] += 1

        # Prepare update for exam_question row
        update_rows.append({
            "id":         eq["id"],
            "is_correct": is_correct
        })

    # Step 4 — bulk update exam_question rows with is_correct
    for row in update_rows:
        supabase.table("exam_question").update(
            {"is_correct": row["is_correct"]}
        ).eq("id", row["id"]).execute()

    # Step 5 — calculate segment scores (percentage)
    def segment_pct(segment_name: str) -> float:
        data = segment_results.get(segment_name)
        if not data or data["total"] == 0:
            return 0.0
        return round(data["correct"] / data["total"] * 100, 2)

    technical_score  = segment_pct("technical")
    analytical_score = segment_pct("analytical")
    domain_score     = segment_pct("domain")
    management_score = segment_pct("management")

    # Step 6 — total score (weighted by question count, not segment average)
    total_score = round(
        total_correct / total_questions * 100, 2
    ) if total_questions > 0 else 0.0

    # Step 7 — store result
    result_data = {
        "session_id":        session_id,
        "candidate_id":      session["candidate_id"],
        "total_score":       total_score,
        "technical_score":   technical_score,
        "analytical_score":  analytical_score,
        "domain_score":      domain_score,
        "management_score":  management_score,
        "hr_shortlisted":    False,
        "created_at":        datetime.now(timezone.utc).isoformat()
    }

    # Check if result already exists (avoid duplicate)
    existing = (
        supabase.table("exam_result")
        .select("id")
        .eq("session_id", session_id)
        .execute()
    )

    if existing.data:
        # Update existing result (re-scoring case)
        result_resp = (
            supabase.table("exam_result")
            .update(result_data)
            .eq("session_id", session_id)
            .execute()
        )
    else:
        result_resp = (
            supabase.table("exam_result")
            .insert(result_data)
            .execute()
        )

    if not result_resp.data:
        return None

    # Step 8 — update candidate status
    supabase.table("candidate").update(
        {"status": "scored"}
    ).eq("id", session["candidate_id"]).execute()

    return {
        "result":          result_resp.data[0],
        "total_questions": total_questions,
        "total_correct":   total_correct,
        "segment_breakdown": {
            seg: {
                "correct":    data["correct"],
                "total":      data["total"],
                "percentage": segment_pct(seg)
            }
            for seg, data in segment_results.items()
        }
    }


def get_result_by_session(session_id: str) -> dict | None:
    """Fetch the score result for a session."""
    response = (
        supabase.table("exam_result")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_result_by_candidate(candidate_id: str) -> dict | None:
    """Fetch the score result for a candidate."""
    response = (
        supabase.table("exam_result")
        .select("*")
        .eq("candidate_id", candidate_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_unanswered_count(session_id: str) -> int:
    """
    Count questions the candidate left unanswered.
    Useful context for HR alongside the score.
    """
    response = (
        supabase.table("exam_question")
        .select("id")
        .eq("session_id", session_id)
        .is_("candidate_answer", "null")
        .execute()
    )
    return len(response.data) if response.data else 0