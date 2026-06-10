import random
import string

from passlib.context import CryptContext

from database.client import supabase


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# =========================
# PASSWORD HELPERS
# =========================

def hash_password(password: str):

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# =========================
# USERNAME
# =========================

def generate_username(email: str):

    base = email.split("@")[0]

    suffix = ''.join(
        random.choices(
            string.ascii_lowercase +
            string.digits,
            k=4
        )
    )

    return f"{base}_{suffix}"


# =========================
# PASSWORD
# =========================

def generate_password(length: int = 8):

    chars = (
        string.ascii_letters +
        string.digits
    )

    return ''.join(
        random.choices(
            chars,
            k=length
        )
    )


# =========================
# ADD BULK CANDIDATES
# =========================

def add_candidates_bulk(
    drive_id: str,
    emails: list
):

    inserted = []

    for email in emails:

        username = generate_username(email)

        plain_password = generate_password()

        password_hash = hash_password(
            plain_password
        )

        response = (
            supabase.table("candidate")
            .insert({
                "drive_id": drive_id,
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "status": "invited"
            })
            .execute()
        )

        if response.data:

            candidate = response.data[0]

            candidate["plain_password"] = (
                plain_password
            )

            inserted.append(candidate)

    return inserted


# =========================
# GET CANDIDATES
# =========================

def get_candidates_by_drive(
    drive_id: str
):

    response = (
        supabase.table("candidate")
        .select("*")
        .eq("drive_id", drive_id)
        .execute()
    )

    return response.data


# =========================
# GET CREDENTIAL SUMMARY
# =========================

def get_credential_summary(
    drive_id: str
):

    candidates = get_candidates_by_drive(
        drive_id
    )

    total = len(candidates)

    invited = len([
        c for c in candidates
        if c["status"] == "invited"
    ])

    exam_started = len([
        c for c in candidates
        if c["status"] == "exam_started"
    ])

    exam_taken = len([
        c for c in candidates
        if c["status"] == "exam_taken"
    ])

    return {
        "total": total,
        "invited": invited,
        "exam_started": exam_started,
        "exam_taken": exam_taken
    }


# =========================
# GET BY ID
# =========================

def get_candidate_by_id(
    candidate_id: str
):

    response = (
        supabase.table("candidate")
        .select("*")
        .eq("id", candidate_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# =========================
# LOGIN
# =========================

def login_candidate(
    username: str,
    password: str
):

    response = (
        supabase.table("candidate")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if not response.data:
        return None

    candidate = response.data[0]

    valid = verify_password(
        password,
        candidate["password_hash"]
    )

    if not valid:
        return None

    return candidate


# =========================
# EXPERIENCE BAND
# =========================

def set_experience_band(
    candidate_id: str,
    experience_band: str
):

    response = (
        supabase.table("candidate")
        .update({
            "experience_band": experience_band,
            "status": "exam_started"
        })
        .eq("id", candidate_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# =========================
# SEGMENTS
# =========================

def get_segments_for_band(
    experience_band: str
):

    mapping = {

        "0-2": [
            "Technical",
            "Analytical"
        ],

        "2-5": [
            "Technical",
            "Analytical",
            "Domain"
        ],

        "5+": [
            "Technical",
            "Analytical",
            "Domain",
            "Management"
        ]
    }

    return mapping.get(
        experience_band,
        [
            "Technical",
            "Analytical"
        ]
    )


# =========================
# CANDIDATE + DRIVE
# =========================

def get_candidate_with_drive(
    candidate_id: str
):

    candidate = get_candidate_by_id(
        candidate_id
    )

    if not candidate:
        return None

    from services.drive_service import (
        get_drive_by_id
    )

    drive = get_drive_by_id(
        candidate["drive_id"]
    )

    if not drive:
        return None

    candidate["drive_role"] = (
        drive["role"]
    )

    return candidate
# =========================
# UNSENT CANDIDATES
# =========================

def get_unsent_candidates(
    drive_id: str
):

    response = (
        supabase.table("candidate")
        .select("*")
        .eq("drive_id", drive_id)
        .eq("status", "invited")
        .execute()
    )

    return response.data


# =========================
# MARK EMAIL SENT
# =========================

def mark_credentials_sent(
    candidate_id: str
):

    response = (
        supabase.table("candidate")
        .update({
            "credentials_sent": True
        })
        .eq("id", candidate_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# =========================
# GET CANDIDATE BY USERNAME
# =========================

def get_candidate_by_username(
    username: str
):

    response = (
        supabase.table("candidate")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

# =========================
# RESET PASSWORD
# =========================

def reset_candidate_password(
    candidate_id: str
):

    new_password = generate_password()

    password_hash = hash_password(
        new_password
    )

    response = (
        supabase.table("candidate")
        .update({
            "password_hash":
                password_hash
        })
        .eq(
            "id",
            candidate_id
        )
        .execute()
    )

    if not response.data:
        return None

    candidate = response.data[0]

    candidate["plain_password"] = (
        new_password
    )

    return candidate