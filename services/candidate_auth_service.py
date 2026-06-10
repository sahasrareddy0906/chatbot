import os

from datetime import (

    datetime,

    timedelta
)

from jose import (

    JWTError,

    jwt
)

from dotenv import (
    load_dotenv
)

from passlib.context import (
    CryptContext
)

from fastapi import (
    HTTPException
)

from database.client import (
    supabase
)


load_dotenv()


SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

ALGORITHM = os.getenv(

    "ALGORITHM",

    "HS256"
)


CANDIDATE_TOKEN_EXPIRE_MINUTES = int(

    os.getenv(

        "CANDIDATE_TOKEN_EXPIRE_MINUTES",

        180
    )
)


pwd_context = CryptContext(

    schemes=["bcrypt"],

    deprecated="auto"
)


# =========================
# CREATE CANDIDATE TOKEN
# =========================

def create_candidate_token(

    candidate_id: str,

    drive_id: str
):

    expire = (

        datetime.utcnow()

        + timedelta(

            minutes=
            CANDIDATE_TOKEN_EXPIRE_MINUTES
        )
    )


    payload = {

        "sub":
            candidate_id,

        "drive_id":
            drive_id,

        "role":
            "candidate",

        "exp":
            expire
    }


    return jwt.encode(

        payload,

        SECRET_KEY,

        algorithm=ALGORITHM
    )


# =========================
# DECODE CANDIDATE TOKEN
# =========================

def decode_candidate_token(
    token: str
):

    try:

        payload = jwt.decode(

            token,

            SECRET_KEY,

            algorithms=[ALGORITHM]
        )


        if payload.get(
            "role"
        ) != "candidate":

            return None


        return payload


    except JWTError:

        return None


# =========================
# CANDIDATE LOGIN
# =========================

def candidate_login(

    username: str,

    password: str
):

    response = (

        supabase.table(
            "candidate"
        )

        .select("*")

        .eq(
            "username",
            username
        )

        .execute()
    )


    if not response.data:

        raise HTTPException(

            status_code=401,

            detail=
                "Invalid username or password"
        )


    candidate = response.data[0]


    # =====================
    # VERIFY PASSWORD
    # =====================

    valid_password = (

        pwd_context.verify(

            password,

            candidate["password_hash"]
        )
    )


    if not valid_password:

        raise HTTPException(

            status_code=401,

            detail=
                "Invalid username or password"
        )


    # =====================
    # CREATE TOKEN
    # =====================

    access_token = (

        create_candidate_token(

            candidate_id=
                candidate["id"],

            drive_id=
                candidate["drive_id"]
        )
    )


    return {

        "access_token":
            access_token,

        "token_type":
            "bearer",

        "candidate":
            candidate
    }