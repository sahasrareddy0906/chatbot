from database.client import supabase


def insert_candidate(
    drive_id,
    email,
    username,
    password_hash,
    experience_band
):

    data = {
        "drive_id": drive_id,
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "experience_band": experience_band,
        "status": "invited"
    }

    response = supabase.table("candidate").insert(data).execute()

    return response.data


def get_candidates_by_drive(drive_id):

    response = (
        supabase
        .table("candidate")
        .select("*")
        .eq("drive_id", drive_id)
        .execute()
    )

    return response.data