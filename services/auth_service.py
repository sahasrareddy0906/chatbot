def hash_password(password: str):

    return password + "_hashed"


def verify_password(
    plain_password: str,
    hashed_password: str
):

    return (
        hashed_password
        ==
        plain_password + "_hashed"
    )


def create_access_token(data: dict):

    return "test_token"


def decode_access_token(token: str):

    return {
        "sub": "test"
    }