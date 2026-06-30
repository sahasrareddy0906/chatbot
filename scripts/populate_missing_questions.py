import requests
import sys

BASE_URL = "http://localhost:8000"

# Import coverage service to get missing combinations
# This requires the backend to be running
def get_missing_combinations_via_api():
    """
    Get missing combinations via the coverage endpoint.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/questions/coverage",
            timeout=10
        )
        data = resp.json()
        coverage = data.get("coverage", [])

        # Find combinations with count < 30
        missing = []
        for item in coverage:
            if item["count"] < 30:
                missing.append({
                    "role": item["role"],
                    "segment": item["segment"],
                    "experience_band": item["experience_band"],
                    "existing": item["count"],
                    "required": 30,
                    "missing": 30 - item["count"]
                })

        return missing
    except Exception as e:
      print(f"Error fetching coverage: {e}")
    sys.exit(1)


def populate_combination(role, segment, band, count):
    """
    Generate and store exactly 'count' questions for a combination.
    """
    payload = {
    "role": role,
    "segment": segment,
    "experience_band": band,
    "skill": role,
    "count": count
}

    try:
        # Override count for this specific request
        # We'll make a custom approach: generate count questions
        resp = requests.post(
            f"{BASE_URL}/questions/generate",
            json=payload,
            timeout=120
        )
        data = resp.json()
        status = data.get("status", "unknown")
        new_count = data.get("new_count", 0)
        total = data.get("total_count", 0)

        return {
            "status": status,
            "new_count": new_count,
            "total": total
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "new_count": 0,
            "total": 0
        }


def main():
    print("="*60)
    print("QUESTION BANK AUTO-POPULATION")
    print("="*60)
    print()

    # Get missing combinations
    missing = get_missing_combinations_via_api()

    if not missing:
        print("✅ Question bank is complete! All combinations have 30+ questions.")
        print()
        return

    print(f"Found {len(missing)} incomplete combinations to populate.\n")

    # Print header
    print(f"{'ROLE':<25} {'SEGMENT':<12} {'BAND':<5} "
          f"{'EXISTING':>8} {'GENERATED':>9} {'FINAL':>6}")
    print("-" * 70)

    total_generated = 0
    successful = 0
    failed = 0

    for gap in missing:
        role = gap["role"]
        segment = gap["segment"]
        band = gap["experience_band"]
        existing = gap["existing"]
        missing_count = gap["missing"]

        # Generate the missing questions
        result = populate_combination(role, segment, band, missing_count)

        status = result["status"]
        new_count = result["new_count"]
        final_total = result["total"]

        if status == "success":
            successful += 1
            total_generated += new_count
            status_icon = "✅"
        elif status == "skipped":
            status_icon = "⏭️"
        else:
            failed += 1
            status_icon = "❌"

        print(f"{role:<25} {segment:<12} {band:<5} "
              f"{existing:>8} {new_count:>9} {final_total:>6}  {status_icon}")

    print()
    print("="*60)
    print("POPULATION SUMMARY")
    print("="*60)
    print(f"Total combinations processed: {len(missing)}")
    print(f"Successfully populated: {successful}")
    print(f"Failed: {failed}")
    print(f"Total questions generated: {total_generated}")
    print()

    # Fetch updated coverage
    try:
        resp = requests.get(
            f"{BASE_URL}/questions/coverage",
            timeout=10
        )
        data = resp.json()
        summary = data.get("summary", {})

        print("="*60)
        print("UPDATED COVERAGE REPORT")
        print("="*60)
        print(f"Total Roles: {summary.get('total_roles', 0)}")
        print(f"Total Combinations: {summary.get('total_combinations', 0)}")
        print(f"Complete Combinations: {summary.get('complete_combinations', 0)}")
        print(f"Incomplete Combinations: {summary.get('incomplete_combinations', 0)}")
        print(f"Total Questions: {summary.get('total_questions', 0)}")
        print()

        if summary.get('incomplete_combinations', 0) == 0:
            print("✅ QUESTION BANK IS NOW COMPLETE!")
        else:
            print(f"⚠️  Still {summary.get('incomplete_combinations', 0)} "
                  f"incomplete combinations remaining.")
        print()

    except Exception as e:
        print(f"Error fetching final coverage: {e}")


if __name__ == "__main__":
    main()
