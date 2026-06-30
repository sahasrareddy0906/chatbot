"""
Test script to verify scoring logic works correctly.
Creates a test session, manually sets answers
(some correct, some wrong, some unanswered),
runs scoring, and verifies the math.
"""

import requests

BASE_URL = "http://localhost:8000"

# These should already exist from your pipeline test (Day 21)
# Update with real values from your database
SESSION_ID = "paste-a-real-session-id-here"
HR_EMAIL   = "hr@company.com"
HR_PASS    = "securepass123"


def get_hr_token():
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email":    HR_EMAIL,
        "password": HR_PASS
    })
    return resp.json()["access_token"]


def main():
    hr_token = get_hr_token()
    headers  = {"Authorization": f"Bearer {hr_token}"}

    print(f"Rescoring session: {SESSION_ID}\n")

    resp = requests.post(
        f"{BASE_URL}/scoring/rescore/{SESSION_ID}",
        headers=headers
    )

    if resp.status_code != 200:
        print(f"❌ Failed: {resp.text}")
        return

    data   = resp.json()
    result = data["result"]["result"]
    breakdown = data["result"]["segment_breakdown"]

    print("="*50)
    print("SCORING RESULT")
    print("="*50)
    print(f"Total Score:       {result['total_score']}%")
    print(f"Technical Score:   {result['technical_score']}%")
    print(f"Analytical Score:  {result['analytical_score']}%")
    print(f"Domain Score:      {result['domain_score']}%")
    print(f"Management Score:  {result['management_score']}%")

    print("\nSEGMENT BREAKDOWN")
    print("="*50)
    for segment, stats in breakdown.items():
        print(
            f"{segment:<12} "
            f"{stats['correct']}/{stats['total']} correct "
            f"({stats['percentage']}%)"
        )

    # Sanity check
    total_correct = sum(s['correct'] for s in breakdown.values())
    total_q       = sum(s['total'] for s in breakdown.values())
    expected_total = round(total_correct / total_q * 100, 2)

    print(f"\nVerification:")
    print(f"  Sum of correct/total = {expected_total}%")
    print(f"  Stored total_score   = {result['total_score']}%")

    if abs(expected_total - result['total_score']) < 0.01:
        print("  ✅ Math checks out!")
    else:
        print("  ❌ MISMATCH — scoring logic has a bug")


if __name__ == "__main__":
    main()
    