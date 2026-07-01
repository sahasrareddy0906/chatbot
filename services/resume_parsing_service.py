from services.resume_storage_service import download_resume_bytes
from services.resume_text_service import extract_resume_text
from services.openai_service import extract_resume_data
from database.client import supabase
import json


def parse_resume(candidate_id: str) -> dict:
    """
    Full resume parsing pipeline for one candidate:
    1. Get resume record from DB
    2. Download file bytes from storage
    3. Extract raw text
    4. Send to OpenAI for structured extraction
    5. Store extracted_skills in resume_match table
    """

    # Step 1 — get resume record
    resume_resp = (
        supabase.table("resume_match")
        .select("*")
        .eq("candidate_id", candidate_id)
        .execute()
    )

    if not resume_resp.data:
        return {
            "success": False,
            "error":   "No resume record found for this candidate"
        }

    resume = resume_resp.data[0]
    storage_path = resume.get("resume_url")

    if not storage_path:
        return {
            "success": False,
            "error":   "No resume file uploaded yet"
        }

    # Step 2 — download file bytes
    file_bytes = download_resume_bytes(storage_path)
    if not file_bytes:
        return {
            "success": False,
            "error":   "Failed to download resume file from storage"
        }

    # Step 3 — extract text
    filename = storage_path.split("/")[-1]
    extraction = extract_resume_text(file_bytes, filename)

    if not extraction["success"]:
        return {
            "success": False,
            "error":   extraction["error"]
        }

    resume_text = extraction["text"]

    # Step 4 — OpenAI structured extraction
    structured_data = extract_resume_data(resume_text)

    if not structured_data:
        return {
            "success": False,
            "error":   "OpenAI failed to parse resume data"
        }

    # Step 5 — store in database
    update_resp = (
        supabase.table("resume_match")
        .update({
            "extracted_skills": json.dumps(structured_data)
        })
        .eq("candidate_id", candidate_id)
        .execute()
    )

    if not update_resp.data:
        return {
            "success": False,
            "error":   "Failed to save extracted data to database"
        }

    return {
        "success":         True,
        "candidate_id":    candidate_id,
        "extracted_data":  structured_data,
        "text_length":     extraction["length"]
    }


def parse_all_resumes_for_drive(drive_id: str) -> dict:
    """
    Parse resumes for all shortlisted candidates in a drive
    who have uploaded a resume but haven't been parsed yet.
    Called when HR clicks "Proceed to Matching".
    """
    # Get all resume records for this drive that have a file
    # but no extracted_skills yet
    resumes_resp = (
        supabase.table("resume_match")
        .select("candidate_id, resume_url, extracted_skills")
        .eq("drive_id", drive_id)
        .execute()
    )

    resumes = resumes_resp.data if resumes_resp.data else []

    to_parse = [
        r for r in resumes
        if r.get("resume_url") and not r.get("extracted_skills")
    ]

    if not to_parse:
        return {
            "message":  "No resumes need parsing — all up to date",
            "parsed":   [],
            "failed":   [],
            "summary":  {"total": 0, "parsed": 0, "failed": 0}
        }

    parsed = []
    failed = []

    for resume in to_parse:
        candidate_id = resume["candidate_id"]
        result = parse_resume(candidate_id)

        if result["success"]:
            parsed.append(candidate_id)
        else:
            failed.append({
                "candidate_id": candidate_id,
                "error":        result["error"]
            })

    return {
        "message": f"Parsed {len(parsed)} of {len(to_parse)} resumes",
        "parsed":  parsed,
        "failed":  failed,
        "summary": {
            "total":  len(to_parse),
            "parsed": len(parsed),
            "failed": len(failed)
        }
    }


def get_extracted_skills(candidate_id: str) -> dict | None:
    """
    Fetch and parse the stored extracted_skills JSON
    for a candidate.
    """
    response = (
        supabase.table("resume_match")
        .select("extracted_skills")
        .eq("candidate_id", candidate_id)
        .execute()
    )

    if not response.data or not response.data[0].get(
        "extracted_skills"
    ):
        return None

    try:
        return json.loads(response.data[0]["extracted_skills"])
    except json.JSONDecodeError:
        return None