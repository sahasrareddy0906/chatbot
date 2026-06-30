import requests

BASE_URL = "http://localhost:8000"

ROLE_SKILLS = {
    "Backend Engineer":         "Python, REST APIs, SQL, System Design",
    "Frontend Engineer":        "JavaScript, React, CSS, Browser APIs",
    "Full Stack Engineer":      "React, Node.js, SQL, APIs, Deployment",
    "Data Engineer":            "Python, SQL, Apache Spark, ETL, Airflow",
    "Data Scientist":           "Python, ML, Statistics, Model Evaluation",
    "DevOps Engineer":          "Docker, Kubernetes, CI/CD, Terraform, AWS",
    "Database Administrator":   "SQL, Indexing, Query Optimisation, Replication",
    "QA Engineer":              "Test Design, Selenium, API Testing, Automation",
    "Business Analyst":         "SQL, Process Mapping, Requirements, Agile",
    "HR Technology Specialist": "HRMS, HR Analytics, Java, Process Automation"
}


def fill_combo(role: str, segment: str, experience_band: str) -> None:
    skill = ROLE_SKILLS.get(role, role)
    payload = {
        "role":            role,
        "skill":           skill,
        "segment":         segment,
        "experience_band": experience_band
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/questions/generate",
            json=payload,
            timeout=60
        )
        data = resp.json()
        status = data.get("status", "unknown")
        total = data.get("total_count", 0)
        print(f"  {status:<8} → total: {total}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def fill_all_gaps(empty_combos: list, low_combos: list) -> None:
    all_gaps = empty_combos + [
        {
            "role":    item["role"],
            "segment": item["segment"],
            "band":    item["band"]
        }
        for item in low_combos
    ]

    if not all_gaps:
        print("✅ No gaps found — bank is complete!")
        return

    print(f"Filling {len(all_gaps)} gaps...\n")
    for gap in all_gaps:
        print(f"{gap['role']} / {gap['segment']} / {gap['band']}")
        fill_combo(
            role=gap["role"],
            segment=gap["segment"],
            experience_band=gap["band"]
        )


EMPTY_COMBOS = []
LOW_COMBOS = []

fill_all_gaps(EMPTY_COMBOS, LOW_COMBOS)
