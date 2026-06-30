import requests

BASE_URL = "http://localhost:8000"

ROLES = [
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

COMBOS = [
    {"experience_band": "0-2", "segment": "technical"},
    {"experience_band": "0-2", "segment": "analytical"},
    {"experience_band": "2-5", "segment": "technical"},
    {"experience_band": "2-5", "segment": "analytical"},
    {"experience_band": "2-5", "segment": "domain"},
    {"experience_band": "5+",  "segment": "technical"},
    {"experience_band": "5+",  "segment": "analytical"},
    {"experience_band": "5+",  "segment": "domain"},
    {"experience_band": "5+",  "segment": "management"}
]

MIN_REQUIRED = 30

results = {
    "ready":       [],
    "low":         [],
    "empty":       [],
    "total_questions": 0
}

print(f"\n{'='*70}")
print(f"{'ROLE':<25} {'SEGMENT':<12} {'BAND':<5} {'COUNT':>6}  STATUS")
print(f"{'='*70}")

for role in ROLES:
    for combo in COMBOS:
        try:
            resp = requests.get(
                f"{BASE_URL}/questions/fetch",
                params={
                    "role":             role,
                    "segment":          combo["segment"],
                    "experience_band":  combo["experience_band"]
                },
                timeout=10
            )

            if resp.status_code == 404:
                count = 0
            else:
                data = resp.json()
                count = data.get("count", 0)

            results["total_questions"] += count

            if count == 0:
                status = "❌ EMPTY"
                results["empty"].append({
                    "role":    role,
                    "segment": combo["segment"],
                    "band":    combo["experience_band"]
                })
            elif count < MIN_REQUIRED:
                status = f"⚠️  LOW ({count}/{MIN_REQUIRED})"
                results["low"].append({
                    "role":    role,
                    "segment": combo["segment"],
                    "band":    combo["experience_band"],
                    "count":   count
                })
            else:
                status = f"✅ READY ({count})"
                results["ready"].append({
                    "role":    role,
                    "segment": combo["segment"],
                    "band":    combo["experience_band"],
                    "count":   count
                })

            print(
                f"{role:<25} "
                f"{combo['segment']:<12} "
                f"{combo['experience_band']:<5} "
                f"{count:>6}  {status}"
            )

        except Exception as e:
            print(
                f"{role:<25} "
                f"{combo['segment']:<12} "
                f"{combo['experience_band']:<5} "
                f"{'ERR':>6}  ❌ {e}"
            )

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Total questions in bank : {results['total_questions']}")
print(f"Ready combos            : {len(results['ready'])}")
print(f"Low count combos        : {len(results['low'])}")
print(f"Empty combos            : {len(results['empty'])}")

total_combos = len(ROLES) * len(COMBOS)
ready_pct = round(len(results['ready']) / total_combos * 100)
print(f"Bank completeness       : {ready_pct}%")

if results["empty"]:
    print(f"\n{'='*70}")
    print("EMPTY COMBOS — MUST FIX:")
    for item in results["empty"]:
        print(f"  {item['role']} / {item['segment']} / {item['band']}")

if results["low"]:
    print(f"\n{'='*70}")
    print("LOW COUNT COMBOS — SHOULD FIX:")
    for item in results["low"]:
        print(f"  {item['role']} / {item['segment']} / {item['band']} — {item['count']} questions")

if ready_pct == 100:
    print(f"\n✅ Question bank is COMPLETE and ready for exams!")
else:
    print(
        f"\n⚠️  Question bank is {ready_pct}% complete. "
        f"Run populate script to fill gaps."
    )
