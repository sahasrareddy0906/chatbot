from fastapi import APIRouter

from pydantic import (
    BaseModel,
    EmailStr
)

from passlib.context import (
    CryptContext
)

from database.client import (
    supabase
)
from services.auth_service import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class RegisterRequest(
    BaseModel
):

    email: EmailStr
    password: str


class LoginRequest(
    BaseModel
):

    email: EmailStr
    password: str


@router.get("/test")
def test():

    return {
        "message": "auth works"
    }


@router.post("/register")
def register(
    request: RegisterRequest
):

    hashed_password = pwd_context.hash(
        request.password
    )

    response = (
        supabase
        .table("hr_user")
        .insert({
            "email":
                request.email,

            "password_hash":
                hashed_password
        })
        .execute()
    )

    return {
        "message":
            "Registration successful"
    }


@router.post("/login")
def login(
    request: LoginRequest
):
    print("===== MY LOGIN ROUTE IS RUNNING =====")
    response = (
        supabase
        .table("hr_user")
        .select("*")
        .eq("email", request.email)
        .execute()
    )

    users = response.data

    if len(users) == 0:

        return {
            "error":
                "User not found"
        }

    user = users[0]

    valid_password = pwd_context.verify(
        request.password,
        user["password_hash"]
    )

    if not valid_password:

        return {
            "error":
                "Invalid password"
        }

    token = create_access_token(
    {
        "sub": str(user["id"]),
        "email": user["email"]
    }
)
    
    print("TOKEN GENERATED:", token)
    return {
    "access_token": token,
    "token_type": "bearer",
    "email": user["email"],
    "id": user["id"]
}