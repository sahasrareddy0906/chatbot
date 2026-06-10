from fastapi import (

    Depends,

    HTTPException,

    status
)

from fastapi.security import (

    HTTPAuthorizationCredentials,

    HTTPBearer
)


from database.client import (
    supabase
)

from services.auth_service import (
    decode_access_token
)

from services.candidate_auth_service import (
    decode_candidate_token
)


security = HTTPBearer()


# =========================
# CURRENT HR
# =========================

def get_current_hr(

    credentials:
    HTTPAuthorizationCredentials = Depends(security)
):

    token = (
        credentials.credentials
    )

    payload = (
        decode_access_token(token)
    )


    if not payload:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "Invalid or expired token",

            headers={
                "WWW-Authenticate":
                    "Bearer"
            }
        )


    hr_id = payload.get(
        "sub"
    )


    if not hr_id:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "Invalid token payload"
        )


    response = (

        supabase.table(
            "hr"
        )

        .select(
            "id, email"
        )

        .eq(
            "id",
            hr_id
        )

        .execute()
    )


    if not response.data:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "HR not found"
        )


    return response.data[0]


# =========================
# CURRENT CANDIDATE
# =========================

def get_current_candidate(

    credentials:
    HTTPAuthorizationCredentials = Depends(security)
):

    token = (
        credentials.credentials
    )

    payload = (
        decode_candidate_token(
            token
        )
    )


    if not payload:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "Invalid or expired candidate token",

            headers={
                "WWW-Authenticate":
                    "Bearer"
            }
        )


    candidate_id = payload.get(
        "sub"
    )

    drive_id = payload.get(
        "drive_id"
    )


    if not candidate_id or not drive_id:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "Token missing required fields"
        )


    response = (

        supabase.table(
            "candidate"
        )

        .select(

            "id, drive_id, username, experience_band, status"
        )

        .eq(
            "id",
            candidate_id
        )

        .execute()
    )


    if not response.data:

        raise HTTPException(

            status_code=
                status.HTTP_401_UNAUTHORIZED,

            detail=
                "Candidate not found"
        )


    return response.data[0]