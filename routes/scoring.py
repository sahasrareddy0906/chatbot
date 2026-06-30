from fastapi import APIRouter, HTTPException, Depends
from services.scoring_service import (
    score_exam_session,
    get_result_by_session,
    get_result_by_candidate,
    get_unanswered_count
)
from services.exam_service import get_exam_session_by_candidate
from dependencies.auth import get_current_candidate, get_current_hr

router = APIRouter(prefix="/scoring", tags=["Scoring"])


@router.get("/my-result")
def get_my_result(candidate=Depends(get_current_candidate)):
    """
    Candidate checks their own result.
    Note: in most flows candidates won't see this —
    only HR sees results. But useful for confirmation
    that submission was scored.
    """
    result = get_result_by_candidate(candidate["id"])

    if not result:
        return {
            "scored": False,
            "message": "Your exam is being processed."
        }

    return {
        "scored":   True,
        "message":  "Your exam has been scored and submitted "
                   "for review.",
        # Don't reveal actual score to candidate —
        # avoid candidates gaming future exam attempts
    }


@router.post("/rescore/{session_id}")
def rescore_session(
    session_id: str,
    hr=Depends(get_current_hr)
):
    """
    HR can trigger a manual rescore.
    Useful if question bank was corrected after exam was taken.
    """
    result = score_exam_session(session_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Session not found or has no questions"
        )

    return {
        "message": "Session rescored successfully",
        "result":  result
    }


@router.get("/session/{session_id}")
def get_session_result(
    session_id: str,
    hr=Depends(get_current_hr)
):
    """
    HR views detailed result for a specific session.
    Includes unanswered count for context.
    """
    result = get_result_by_session(session_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No result found for this session. "
                   "Exam may not be submitted yet."
        )

    unanswered = get_unanswered_count(session_id)

    return {
        "result":     result,
        "unanswered": unanswered
    }