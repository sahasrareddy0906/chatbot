import requests

BASE_URL = "http://localhost:8000"

MANAGEMENT_ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data Engineer",
    "Data Scientist",
    "DevOps Engineer",
    "Database Administrator",
    "QA Engineer",
    "Business Analyst",
    "HR Technology Specialist"
]


def populate_role(role: str) -> None:
    payload = {
        "role": role,
        "segment": "management",
        "experience_band": "5+",
        "skill": role
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/questions/generate",
            json=payload,
            timeout=120
        )
        data = resp.json()
        status = data.get("status", "unknown")
        total = data.get("total_count")
        new_count = data.get("new_count")

        print(f"{role}")
        print(f"STATUS: {status}")
        print(f"TOTAL QUESTIONS: {total if total is not None else new_count}")
        print("---")
    except Exception as exc:
        print(f"{role}")
        print("STATUS: error")
        print(f"TOTAL QUESTIONS: 0")
        print(f"ERROR: {exc}")
        print("---")


def main() -> None:
    print("Populating management questions for senior roles:\n")

    for role in MANAGEMENT_ROLES:
        populate_role(role)


if __name__ == "__main__":
    main()
