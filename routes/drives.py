from fastapi import (

    APIRouter,

    HTTPException,

    Depends
)
from dependencies.auth import (
    get_current_hr
)
from pydantic import (
    BaseModel
)


from services.drive_service import (

    create_drive,

    get_drive_by_id,

    get_drives_by_hr,

    close_drive
)


from services.candidate_service import (

    add_candidates_bulk,

    get_candidates_by_drive,

    get_credential_summary
)


from services.credential_service import (

    prepare_credential_packages,

    prepare_single_credential_package
)

from services.email_service import (

    send_bulk_credentials,

    send_credential_email
)

from services.candidate_service import (
    mark_credentials_sent
)

router = APIRouter(

    prefix="/drives",

    tags=["Drives"]
)


# =========================
# REQUEST MODELS
# =========================

class CreateDriveRequest(
    BaseModel
):

    role: str

    job_description: str


class AddCandidatesRequest(
    BaseModel
):

    emails: list[str]


# =========================
# CREATE DRIVE
# =========================

@router.post("/")
def create_hiring_drive(

    request: CreateDriveRequest
):

    if len(

        request.job_description
        .strip()

    ) < 50:

        raise HTTPException(

            status_code=400,

            detail=
                "Job description too short"
        )


    drive = create_drive(

        "6a861161-0be2-40b1-bbbc-cfed79423818",

        request.role,

        request.job_description
    )


    if not drive:

        raise HTTPException(

            status_code=500,

            detail=
                "Failed to create drive"
        )


    return {

        "message":
            "Hiring drive created",

        "drive":
            drive
    }


# =========================
# LIST DRIVES
# =========================

@router.get("/")
def list_drives():

    drives = get_drives_by_hr(

        "6a861161-0be2-40b1-bbbc-cfed79423818"
    )

    return {

        "drives":
            drives
    }


# =========================
# GET DRIVE
# =========================

@router.get(
    "/{drive_id}"
)
def get_drive(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    return drive


# =========================
# ADD CANDIDATES
# =========================

@router.post(
    "/{drive_id}/candidates"
)
def add_candidates(

    drive_id: str,

    request: AddCandidatesRequest
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    if drive["status"] == "closed":

        raise HTTPException(

            status_code=400,

            detail=
                "Drive is closed"
        )


    result = add_candidates_bulk(

        drive_id,

        request.emails
    )


    return result


# =========================
# LIST CANDIDATES
# =========================

@router.get(
    "/{drive_id}/candidates"
)
def list_candidates(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    candidates = (

        get_candidates_by_drive(
            drive_id
        )
    )


    return {

        "candidates":
            candidates,

        "count":
            len(candidates)
    }


# =========================
# CLOSE DRIVE
# =========================

@router.patch(
    "/{drive_id}/close"
)
def close_hiring_drive(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    result = close_drive(
        drive_id
    )


    return {

        "message":
            "Drive closed",

        "drive":
            result
    }


# =========================
# CREDENTIAL SUMMARY
# =========================

@router.get(
    "/{drive_id}/credentials/summary"
)
def credential_summary(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    summary = (

        get_credential_summary(
            drive_id
        )
    )


    return summary


# =========================
# PREPARE CREDENTIALS
# =========================

@router.post(
    "/{drive_id}/credentials/prepare"
)
def prepare_credentials(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    packages = (

        prepare_credential_packages(
            drive_id
        )
    )


    return {

        "message":
            f"Prepared {len(packages)} credential packages",

        "packages":
            packages
    }


# =========================
# RESEND CREDENTIALS
# =========================

@router.post(
    "/{drive_id}/candidates/{candidate_id}/resend"
)
def resend_credentials(

    drive_id: str,

    candidate_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail=
                "Drive not found"
        )


    package = (

        prepare_single_credential_package(
            candidate_id
        )
    )


    if not package:

        raise HTTPException(

            status_code=404,

            detail=
                "Candidate not found"
        )


    return {

        "message":
            "Credential package ready",

        "package":
            package
    }

# =========================
# SEND ALL CREDENTIALS
# =========================

@router.post(
    "/{drive_id}/credentials/send"
)
def send_credentials(

    drive_id: str,

    hr=Depends(
        get_current_hr
    )
):

    drive = (
        get_drive_by_id(
            drive_id
        )
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail="Drive not found"
        )


    if drive["hr_id"] != hr["id"]:

        raise HTTPException(

            status_code=403,

            detail="Not your drive"
        )


    # =====================
    # PREPARE PACKAGES
    # =====================

    packages = (

        prepare_credential_packages(
            drive_id
        )
    )


    if not packages:

        return {

            "message":

                "No pending candidates",

            "summary": {

                "total": 0,

                "sent": 0,

                "failed": 0
            }
        }


    # =====================
    # SEND EMAILS
    # =====================

    result = (

        send_bulk_credentials(
            packages
        )
    )


    # =====================
    # MARK SENT
    # =====================

    for candidate_id in result["sent"]:

        mark_credentials_sent(
            candidate_id
        )


    # =====================
    # RESPONSE
    # =====================

    return {

        "message":

            f"Credentials sent to "
            f"{result['summary']['sent']} candidates",


        "summary":

            result["summary"],


        "failed":

            result["failed"]
    }


# =========================
# RESEND SINGLE EMAIL
# =========================

@router.post(
    "/{drive_id}/candidates/{candidate_id}/resend"
)
def resend_credentials(

    drive_id: str,

    candidate_id: str,

    hr=Depends(
        get_current_hr
    )
):

    drive = (
        get_drive_by_id(
            drive_id
        )
    )


    if not drive:

        raise HTTPException(

            status_code=404,

            detail="Drive not found"
        )


    if drive["hr_id"] != hr["id"]:

        raise HTTPException(

            status_code=403,

            detail="Not your drive"
        )


    package = (

        prepare_single_credential_package(
            candidate_id
        )
    )


    if not package:

        raise HTTPException(

            status_code=404,

            detail="Candidate not found"
        )


    success = (

        send_credential_email(

            candidate_email=
                package["email"],

            username=
                package["username"],

            plain_password=
                package["plain_password"],

            drive_role=
                package["drive_role"]
        )
    )


    if success:

        mark_credentials_sent(
            candidate_id
        )

        return {

            "message":

                f"Credentials resent to "
                f"{package['email']}"
        }


    raise HTTPException(

        status_code=500,

        detail=

            f"Failed to send email to "
            f"{package['email']}"
    )