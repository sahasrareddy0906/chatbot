import os

from sendgrid import (
    SendGridAPIClient
)

from sendgrid.helpers.mail import (
    Mail
)

from dotenv import (
    load_dotenv
)


load_dotenv()


SENDGRID_API_KEY = os.getenv(
    "SENDGRID_API_KEY"
)

FROM_EMAIL = os.getenv(
    "SENDGRID_FROM_EMAIL"
)

FROM_NAME = os.getenv(

    "SENDGRID_FROM_NAME",

    "AI Recruitment System"
)

EXAM_URL = os.getenv(

    "EXAM_URL",

    "http://localhost:5173/candidate/login"
)


# =========================
# BUILD EMAIL HTML
# =========================

def build_credential_email(

    username: str,

    plain_password: str,

    drive_role: str,

    exam_url: str
) -> str:

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">

  <style>

    body {{
      font-family: Arial, sans-serif;
      background: #f4f4f4;
      margin: 0;
      padding: 0;
    }}

    .container {{
      max-width: 560px;
      margin: 40px auto;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}

    .header {{
      background: #1a1a2e;
      color: #ffffff;
      padding: 28px 32px;
    }}

    .header h1 {{
      margin: 0;
      font-size: 20px;
    }}

    .body {{
      padding: 32px;
      color: #333333;
    }}

    .credential-box {{
      background: #f8f8f8;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
    }}

    .credential-row {{
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #eeeeee;
    }}

    .credential-row:last-child {{
      border-bottom: none;
    }}

    .cred-label {{
      color: #777777;
      font-size: 13px;
    }}

    .cred-value {{
      font-weight: bold;
      font-family: monospace;
    }}

    .btn {{
      display: inline-block;
      background: #4f46e5;
      color: white !important;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 6px;
      margin-top: 20px;
    }}

    .warning {{
      background: #fff8e1;
      border-left: 4px solid #f59e0b;
      padding: 12px;
      margin-top: 20px;
    }}

    .footer {{
      background: #f4f4f4;
      padding: 20px;
      text-align: center;
      font-size: 12px;
      color: #777777;
    }}

  </style>

</head>

<body>

  <div class="container">

    <div class="header">

      <h1>
        You've been invited to take an exam
      </h1>

      <p>
        Role: {drive_role}
      </p>

    </div>

    <div class="body">

      <p>Hello,</p>

      <p>
        You have been shortlisted for the role of
        <strong>{drive_role}</strong>.
      </p>

      <p>
        Use the credentials below to access your exam.
      </p>

      <div class="credential-box">

        <div class="credential-row">

          <span class="cred-label">
            Username
          </span>

          <span class="cred-value">
            {username}
          </span>

        </div>

        <div class="credential-row">

          <span class="cred-label">
            Password
          </span>

          <span class="cred-value">
            {plain_password}
          </span>

        </div>

      </div>

      <a href="{exam_url}" class="btn">
        Open Exam Portal
      </a>

      <div class="warning">

        Keep these credentials private.
        Do not share them with anyone.

      </div>

      <p>
        Once logged in, select your experience band
        and begin the assessment.
      </p>

    </div>

    <div class="footer">

      AI Recruitment System

    </div>

  </div>

</body>
</html>
"""


# =========================
# SEND SINGLE EMAIL
# =========================

def send_credential_email(

    candidate_email: str,

    username: str,

    plain_password: str,

    drive_role: str
) -> bool:

    try:

        html_content = (

            build_credential_email(

                username=
                    username,

                plain_password=
                    plain_password,

                drive_role=
                    drive_role,

                exam_url=
                    EXAM_URL
            )
        )


        message = Mail(

            from_email=(
                FROM_EMAIL,
                FROM_NAME
            ),

            to_emails=
                candidate_email,

            subject=
                f"Your Exam Invitation — {drive_role}",

            html_content=
                html_content
        )


        sg = SendGridAPIClient(
            SENDGRID_API_KEY
        )

        response = sg.send(
            message
        )


        if response.status_code in [

            200,
            201,
            202
        ]:

            print(
                f"✅ Email sent to {candidate_email}"
            )

            return True


        print(

            f"❌ SendGrid error "
            f"{response.status_code}"
        )

        return False


    except Exception as e:

        print(
            f"❌ Email failed: {e}"
        )

        return False


# =========================
# BULK SEND
# =========================

def send_bulk_credentials(
    packages: list
):

    sent = []

    failed = []


    for pkg in packages:

        success = (

            send_credential_email(

                candidate_email=
                    pkg["email"],

                username=
                    pkg["username"],

                plain_password=
                    pkg["plain_password"],

                drive_role=
                    pkg["drive_role"]
            )
        )


        if success:

            sent.append(
                pkg["candidate_id"]
            )

        else:

            failed.append(
                pkg["email"]
            )


    return {

        "sent":
            sent,

        "failed":
            failed,

        "summary": {

            "total":
                len(packages),

            "sent":
                len(sent),

            "failed":
                len(failed)
        }
    }