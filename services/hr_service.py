from database.client import supabase


def get_hr_by_email(email: str):

    return None


def register_hr(
    email: str,
    password: str
):

    response = (
        supabase
        .table("hr_user")
        .insert({
            "email": email,
            "password_hash": "test123"
        })
        .execute()
    )

    return response.data[0]


def login_hr(
    email: str,
    password: str
):

    access_token = create_access_token(
    {
        "sub": response.data[0]["id"]
    }
)

    return {
    "access_token": access_token,
    "token_type": "bearer",
    "email": response.data[0]["email"],
    "id": response.data[0]["id"]
}