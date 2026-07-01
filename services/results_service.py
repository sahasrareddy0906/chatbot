from database.client import supabase


def get_ranked_results(drive_id: str) -> list:
    """
    Fetch all scored candidates for a drive, ranked by total_score.
    Joins candidate info, exam result, and proctoring status
    into a single flat structure for the HR dashboard.
    """

    # Step 1 — get all candidates for this drive
    candidates_resp = (
        supabase.table("candidate")
        .select("id, email, username, experience_band, status")
        .eq("drive_id", drive_id)
        .execute()
    )

    candidates = candidates_resp.data if candidates_resp.data else []

    if not candidates:
        return []

    candidate_ids = [c["id"] for c in candidates]

    # Step 2 — get exam results for these candidates
    results_resp = (
        supabase.table("exam_result")
        .select("*")
        .in_("candidate_id", candidate_ids)
        .execute()
    )

    results = results_resp.data if results_resp.data else []
    results_by_candidate = {r["candidate_id"]: r for r in results}

    # Step 3 — get exam sessions for proctoring status
    sessions_resp = (
        supabase.table("exam_session")
        .select("candidate_id, proctoring_status, violation_count, "
                "start_time, end_time, submitted")
        .in_("candidate_id", candidate_ids)
        .execute()
    )

    sessions = sessions_resp.data if sessions_resp.data else []
    sessions_by_candidate = {s["candidate_id"]: s for s in sessions}

    # Step 4 — merge everything into one structure per candidate
    merged = []

    for candidate in candidates:
        cid    = candidate["id"]
        result = results_by_candidate.get(cid)
        session = sessions_by_candidate.get(cid)

        # Skip candidates who haven't taken the exam yet
        if not result:
            merged.append({
                "candidate_id":      cid,
                "email":             candidate["email"],
                "username":          candidate["username"],
                "experience_band":   candidate["experience_band"],
                "status":            candidate["status"],
                "has_result":        False,
                "total_score":       None,
                "technical_score":   None,
                "analytical_score":  None,
                "domain_score":      None,
                "management_score":  None,
                "hr_shortlisted":    False,
                "proctoring_status": None,
                "violation_count":   0
            })
            continue

        merged.append({
            "candidate_id":      cid,
            "email":             candidate["email"],
            "username":          candidate["username"],
            "experience_band":   candidate["experience_band"],
            "status":            candidate["status"],
            "has_result":        True,
            "total_score":       result["total_score"],
            "technical_score":   result["technical_score"],
            "analytical_score":  result["analytical_score"],
            "domain_score":      result["domain_score"],
            "management_score":  result["management_score"],
            "hr_shortlisted":    result.get("hr_shortlisted", False),
            "result_id":         result["id"],
            "proctoring_status": (
                session.get("proctoring_status") if session else None
            ),
            "violation_count": (
                session.get("violation_count", 0) if session else 0
            )
        })

    # Step 5 — sort by total_score descending
    # candidates without results go to the bottom
    merged.sort(
        key=lambda x: (
            x["total_score"] is None,   # False sorts before True
            -(x["total_score"] or 0)
        )
    )

    # Step 6 — add rank number
    for idx, c in enumerate(merged):
        c["rank"] = idx + 1 if c["has_result"] else None

    return merged


def get_drive_stats(drive_id: str) -> dict:
    """
    Summary stats for the drive — shown at top of results page.
    """
    results = get_ranked_results(drive_id)

    total_candidates  = len(results)
    scored_candidates = sum(1 for c in results if c["has_result"])
    shortlisted       = sum(
        1 for c in results if c.get("hr_shortlisted")
    )

    scores = [
        c["total_score"] for c in results if c["has_result"]
    ]

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0

    suspicious_count = sum(
        1 for c in results
        if c.get("proctoring_status") == "suspicious"
    )

    return {
        "total_candidates":  total_candidates,
        "scored_candidates": scored_candidates,
        "pending_candidates": total_candidates - scored_candidates,
        "shortlisted":       shortlisted,
        "avg_score":         avg_score,
        "max_score":         max_score,
        "min_score":         min_score,
        "suspicious_proctoring_count": suspicious_count
    }


def shortlist_candidates(result_ids: list) -> dict:
    print("SHORTLIST IDS:", result_ids)
    """
    Mark a list of exam_result rows as hr_shortlisted = true.
    Called when HR selects candidates and clicks Shortlist.
    """
    updated = []
    failed  = []

    for result_id in result_ids:
        response = (
            supabase.table("exam_result")
            .update({"hr_shortlisted": True})
            .eq("id", result_id)
            .execute()
        )
        if response.data:
            updated.append(result_id)
        else:
            failed.append(result_id)

    return {
        "updated": updated,
        "failed":  failed,
        "summary": {
            "total":   len(result_ids),
            "updated": len(updated),
            "failed":  len(failed)
        }
    }


def unshortlist_candidates(result_ids: list) -> dict:
    """
    Reverse a shortlist decision.
    Useful if HR changes their mind before moving to resume stage.
    """
    updated = []

    for result_id in result_ids:
        response = (
            supabase.table("exam_result")
            .update({"hr_shortlisted": False})
            .eq("id", result_id)
            .execute()
        )
        if response.data:
            updated.append(result_id)

    return {"updated": updated}