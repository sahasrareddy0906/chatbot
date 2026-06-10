from services.candidate_service import (

    get_unsent_candidates,

    mark_credentials_sent,

    reset_candidate_password,

    get_candidate_by_id
)

from services.drive_service import (
    get_drive_by_id
)


# =========================
# PREPARE ALL PACKAGES
# =========================

def prepare_credential_packages(
    drive_id: str
):

    drive = get_drive_by_id(
        drive_id
    )


    if not drive:

        return []


    unsent = (

        get_unsent_candidates(
            drive_id
        )
    )


    packages = []


    for candidate in unsent:

        # ---------------------
        # RESET PASSWORD
        # ---------------------

        updated = (

            reset_candidate_password(
                candidate["id"]
            )
        )


        if not updated:

            continue


        package = {

            "candidate_id":
                candidate["id"],

            "email":
                candidate["email"],

            "username":
                candidate["username"],

            "plain_password":
                updated["plain_password"],

            "drive_role":
                drive["role"],

            "exam_url":
                "http://localhost:5173/exam"
        }


        packages.append(
            package
        )


    return packages


# =========================
# PREPARE SINGLE PACKAGE
# =========================

def prepare_single_credential_package(
    candidate_id: str
):

    updated = (

        reset_candidate_password(
            candidate_id
        )
    )


    if not updated:

        return None


    candidate = (

        get_candidate_by_id(
            candidate_id
        )
    )


    if not candidate:

        return None


    drive = (

        get_drive_by_id(
            candidate["drive_id"]
        )
    )


    if not drive:

        return None


    return {

        "candidate_id":
            candidate_id,

        "email":
            candidate["email"],

        "username":
            candidate["username"],

        "plain_password":
            updated["plain_password"],

        "drive_role":
            drive["role"],

        "exam_url":
            "http://localhost:5173/exam"
    }