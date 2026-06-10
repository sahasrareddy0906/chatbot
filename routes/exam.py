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
    submit_exam
)

router = APIRouter(
    prefix="/exam",
    tags=["Exam"]
)


class SubmitExamRequest(
    BaseModel
):
    answers: dict


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

@router.post("/submit")
def submit_candidate_exam(

    request: SubmitExamRequest,

    candidate=Depends(
        get_current_candidate
    )
):

    return submit_exam(
        candidate["id"],
        request.answers
    )