from fastapi import (

    APIRouter,

    HTTPException,

    Depends
)

from pydantic import (
    BaseModel
)


from services.candidate_service import (

    login_candidate,

    set_experience_band,

    get_segments_for_band
)

from services.candidate_auth_service import (
    create_candidate_token
)

from dependencies.auth import (
    get_current_candidate
)


router = APIRouter(

    prefix="/candidate",

    tags=["Candidate Auth"]
)


# =========================
# REQUEST MODELS
# =========================

class CandidateLoginRequest(
    BaseModel
):

    username: str

    password: str


class ExperienceBandRequest(
    BaseModel
):

    experience_band: str


# =========================
# LOGIN
# =========================

@router.post("/login")
def candidate_login(

    request:
    CandidateLoginRequest
):

    candidate = (

        login_candidate(

            request.username,

            request.password
        )
    )


    if not candidate:

        raise HTTPException(

            status_code=401,

            detail=
                "Invalid username or password"
        )


    if candidate["status"] == "exam_taken":

        raise HTTPException(

            status_code=403,

            detail=
                "You have already submitted your exam"
        )


    token = (

        create_candidate_token(

            candidate_id=
                candidate["id"],

            drive_id=
                candidate["drive_id"]
        )
    )


    return {

        "access_token":
            token,

        "token_type":
            "bearer",

        "candidate_id":
            candidate["id"],

        "username":
            candidate["username"],

        "status":
            candidate["status"],

        "experience_band":
            candidate.get(
                "experience_band"
            )
    }


# =========================
# EXPERIENCE BAND
# =========================

@router.post(
    "/experience-band"
)
def select_experience_band(

    request:
    ExperienceBandRequest,

    candidate=Depends(
        get_current_candidate
    )
):

    updated = (

        set_experience_band(

            candidate["id"],

            request.experience_band
        )
    )


    if not updated:

        raise HTTPException(

            status_code=400,

            detail=
                "Cannot set experience band"
        )


    segments = (

        get_segments_for_band(

            request.experience_band
        )
    )


    return {

        "message":
            "Experience band set successfully",

        "experience_band":
            request.experience_band,

        "segments":
            segments,

        "question_count":
            len(segments) * 10,

        "total_questions":
            len(segments) * 10
    }


# =========================
# CURRENT CANDIDATE
# =========================

@router.get("/me")
def get_candidate_me(

    candidate=Depends(
        get_current_candidate
    )
):

    segments = (

        get_segments_for_band(

            candidate.get(

                "experience_band",

                "0-2"
            )
        )
    )


    return {

        "candidate":
            candidate,

        "segments":
            segments,

        "ready":
            candidate["status"]
            ==
            "exam_started"
    }