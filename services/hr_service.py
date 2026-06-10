from database.client import supabase

from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)


def get_hr_by_email(
    email: str
):

    response = (
        supabase
        .table("hr_user")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if response.data:

        return response.data[0]

    return None


def register_hr(
    email: str,
    password: str
):

    existing = get_hr_by_email(
        email
    )

    if existing:

        return None

    hashed = hash_password(
        password
    )

    response = (
        supabase
        .table("hr_user")
        .insert({
            "email": email,

            "password_hash":
                hashed
        })
        .execute()
    )

    if response.data:

        return response.data[0]

    return None


def login_hr(
    email: str,
    password: str
):

    hr = get_hr_by_email(
        email
    )

    if not hr:

        return None

    valid = verify_password(
        password,
        hr["password_hash"]
    )

    if not valid:

        return None

    token = create_access_token({
        "sub": hr["id"]
    })

    return {

        "access_token":
            token,

        "token_type":
            "bearer",

        "hr_id":
            hr["id"],

        "email":
            hr["email"]
    }