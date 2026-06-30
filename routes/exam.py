from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel

from dependencies.auth import (
    get_current_candidate
)

from services.candidate_service import (
    get_candidate_with_drive
)

from services.exam_service import (
    start_exam,
    submit_exam,
    save_answer,
    get_answered_count,
    get_exam_progress,
    get_exam_result,
    get_latest_candidate_result,
    get_exam_results,
    shortlist_candidate,
    get_exam_session_by_candidate,
    is_session_expired,
    get_time_remaining_seconds,
    auto_submit_expired_sessions
)
from services.proctoring_service import (
    log_proctoring_event,
    get_proctoring_summary,
    finalise_proctoring
)

router = APIRouter(
    prefix="/exam",
    tags=["Exam"]
)


class SubmitExamRequest(
    BaseModel
):
    session_id: str


class SaveAnswerRequest(
    BaseModel
):
    session_id: str

    question_id: str

    answer: str

class ProctoringEventRequest(BaseModel):
    event_type: str  # "present" / "face_absent" / "multiple_faces"

# =========================
# START EXAM
# =========================

@router.post("/start")
def start_candidate_exam(

    candidate=Depends(
        get_current_candidate
    )
):

    candidate_data = (
        get_candidate_with_drive(
            candidate["id"]
        )
    )

    if not candidate_data:

        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    if not candidate_data.get(
        "experience_band"
    ):

        raise HTTPException(
            status_code=400,
            detail="Experience band not selected"
        )

    response = start_exam(

        candidate_id=
            candidate_data["id"],

        drive_id=
            candidate_data["drive_id"],

        experience_band=
            candidate_data["experience_band"],

        role=
            candidate_data["drive_role"]
    )

    if response.get("error"):

        raise HTTPException(
            status_code=400,
            detail=response["error"]
        )

    return response


# =========================
# SUBMIT EXAM
# =========================

@router.get("/time")
def get_time_remaining(
    candidate=Depends(
        get_current_candidate
    )
):

    auto_submit_expired_sessions()

    session = get_exam_session_by_candidate(
        candidate["id"]
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="No active session"
        )

    if is_session_expired(session):
        submit_exam(
            session["id"],
            candidate["id"]
        )

        return {
            "time_remaining": 0,
            "expired": True,
            "submitted": True
        }

    return {
        "time_remaining": get_time_remaining_seconds(session),
        "expired": False,
        "submitted": session.get("submitted", False),
        "end_time": session.get("end_time")
    }


@router.post("/force-submit-expired")
def force_submit_expired(
    candidate=Depends(
        get_current_candidate
    )
):

    session = get_exam_session_by_candidate(
        candidate["id"]
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="No active session"
        )

    if session.get("submitted"):
        return {
            "submitted": True,
            "message": "Already submitted"
        }

    if not is_session_expired(session):
        raise HTTPException(
            status_code=400,
            detail="Session not expired"
        )

    submit_exam(
        session["id"],
        candidate["id"]
    )

    return {
        "submitted": True,
        "message": "Exam auto-submitted due to time expiry"
    }


@router.post("/submit")
def submit_candidate_exam(

    request: SubmitExamRequest,

    candidate=Depends(
        get_current_candidate
    )
):

    response = submit_exam(
        request.session_id,
        candidate["id"]
    )

    if response.get("error"):
        raise HTTPException(
            status_code=400,
            detail=response["error"]
        )

    return response


@router.post("/answer")
def save_candidate_answer(

    request: SaveAnswerRequest,

    candidate=Depends(
        get_current_candidate
    )
):

    answer = save_answer(
        request.session_id,
        request.question_id,
        request.answer
    )

    if not answer:
        raise HTTPException(
            status_code=400,
            detail="Invalid answer or session expired"
        )

    return {
        "message": "saved"
    }


@router.get("/progress/{session_id}")
def exam_progress(
    session_id: str,
    candidate=Depends(
        get_current_candidate
    )
):

    progress = get_exam_progress(
        session_id
    )

    if progress is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return progress

@router.get("/results/me")
def exam_result_me(
    candidate=Depends(
        get_current_candidate
    )
):

    result = get_latest_candidate_result(
        candidate["id"]
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Result not found"
        )

    return result

@router.get("/results/{session_id}")
def exam_result(
    session_id: str,
    candidate=Depends(
        get_current_candidate
    )
):

    result = get_exam_result(
        session_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Result not found"
        )

    if result["candidate_id"] != candidate["id"]:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized"
        )

    return result



@router.get("/results")
def exam_results():

    return get_exam_results()
@router.post(
    "/results/{result_id}/shortlist"
)
def shortlist_result(
    result_id: str
):

    result = shortlist_candidate(
        result_id
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Result not found"
        )

    return {
        "success": True
    }
@router.post("/proctor/event")
def log_event(
    request: ProctoringEventRequest,
    candidate=Depends(get_current_candidate)
):
    """
    Called by frontend every 5 seconds with detection result.
    Logs event and returns current violation status.
    """
    valid_events = ["present", "face_absent", "multiple_faces"]
    if request.event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type. Must be one of: "
                   f"{valid_events}"
        )

    session = get_exam_session_by_candidate(candidate["id"])
    if not session:
        raise HTTPException(
            status_code=404,
            detail="No active session"
        )

    if session["is_submitted"]:
        return {"logged": False, "reason": "Exam already submitted"}

    result = log_proctoring_event(
        session_id=session["id"],
        candidate_id=candidate["id"],
        event_type=request.event_type
    )

    return result or {"logged": False}


@router.get("/proctor/summary/{session_id}")
def proctoring_summary(
    session_id: str,
    candidate=Depends(get_current_candidate)
):
    """Returns proctoring summary for a session."""
    summary = get_proctoring_summary(session_id)
    return summary
