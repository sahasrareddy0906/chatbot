from database.client import (
    supabase
)


# =========================
# CREATE DRIVE
# =========================

def create_drive(

    hr_id: str,

    role: str,

    job_description: str
):

    response = (

        supabase.table(
            "hiring_drive"
        )

        .insert({

            "hr_id":
                hr_id,

            "role":
                role,

            "job_description":
                job_description,

            "status":
                "active"
        })

        .execute()
    )


    return (

        response.data[0]

        if response.data

        else None
    )


# =========================
# GET DRIVES BY HR
# =========================

def get_drives_by_hr(
    hr_id: str
):

    response = (

        supabase.table(
            "hiring_drive"
        )

        .select("*")

        .eq(
            "hr_id",
            hr_id
        )

        .order(
            "created_at",

            desc=True
        )

        .execute()
    )


    return (

        response.data

        if response.data

        else []
    )


# =========================
# GET DRIVE BY ID
# =========================

def get_drive_by_id(
    drive_id: str
):

    response = (

        supabase.table(
            "hiring_drive"
        )

        .select("*")

        .eq(
            "id",
            drive_id
        )

        .execute()
    )


    return (

        response.data[0]

        if response.data

        else None
    )


# =========================
# CLOSE DRIVE
# =========================

def close_drive(
    drive_id: str
):

    response = (

        supabase.table(
            "hiring_drive"
        )

        .update({

            "status":
                "closed"
        })

        .eq(
            "id",
            drive_id
        )

        .execute()
    )


    return (

        response.data[0]

        if response.data

        else None
    )