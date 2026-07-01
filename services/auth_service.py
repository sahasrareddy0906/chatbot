from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "abc123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_access_token(data: dict):
    print("AUTH SERVICE EXECUTED")
    print(data)

    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=60)

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    print("JWT =", token)

    return token


def decode_access_token(token: str):
    print("DECODE CALLED")

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )