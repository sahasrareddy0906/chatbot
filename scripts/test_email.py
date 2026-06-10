from services.email_service import (
    send_credential_email
)


result = send_credential_email(

    candidate_email=
        "udaysunkaraboina0909@gmail.com",

    username=
        "test_user_01",

    plain_password=
        "TestPass123",

    drive_role=
        "Backend Engineer"
)


print(

    "✅ Sent!"

    if result

    else

    "❌ Failed"
)