from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from services.resume_storage_service import (
    upload_resume_file,
    get_resume_signed_url,
    delete_resume_file
)
from services.resume_match_service import (
    create_resume_record,
    get_resume_by_candidate,
    get_shortlisted_candidates_with_resume_status
)
from services.drive_service import get_drive_by_id
from services.candidate_service import get_candidate_by_id
from dependencies.auth import get_current_hr

from services.resume_parsing_service import (
    parse_resume,
    parse_all_resumes_for_drive,
    get_extracted_skills
)
router = APIRouter(prefix="/resumes", tags=["Resumes"])

MAX_FILE_SIZE_MB = 5
ALLOWED_TYPES    = ["pdf", "doc", "docx"]


@router.get("/{drive_id}/shortlisted")
def get_shortlisted_for_resume_upload(
    drive_id: str,
    hr=Depends(get_current_hr)
):
    """
    Returns shortlisted candidates with resume upload status.
    Main data source for the resume upload page.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    candidates = get_shortlisted_candidates_with_resume_status(
        drive_id
    )

    uploaded_count = sum(1 for c in candidates if c["has_resume"])

    return {
        "candidates":       candidates,
        "total":            len(candidates),
        "uploaded":         uploaded_count,
        "remaining":        len(candidates) - uploaded_count,
        "all_uploaded":     (
            uploaded_count == len(candidates) and len(candidates) > 0
        )
    }


@router.post("/{drive_id}/candidates/{candidate_id}/upload")
async def upload_resume(
    drive_id: str,
    candidate_id: str,
    file: UploadFile = File(...),
    hr=Depends(get_current_hr)
):
    """
    HR uploads a resume file for one shortlisted candidate.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404, detail="Candidate not found"
        )
    if candidate["drive_id"] != drive_id:
        raise HTTPException(
            status_code=400,
            detail="Candidate does not belong to this drive"
        )

    # Validate file type
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_TYPES}"
        )

    # Read and validate size
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB"
        )

    # Upload to storage
    upload_result = upload_resume_file(
        candidate_id=candidate_id,
        drive_id=drive_id,
        file_bytes=file_bytes,
        original_filename=file.filename
    )

    if not upload_result or upload_result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=upload_result.get("error", "Upload failed")
            if upload_result else "Upload failed"
        )

    # Create resume_match record
    resume_record = create_resume_record(
        candidate_id=candidate_id,
        drive_id=drive_id,
        storage_path=upload_result["storage_path"],
        filename=file.filename
    )

    if not resume_record:
        raise HTTPException(
            status_code=500,
            detail="Failed to save resume record"
        )

    return {
        "message":  f"Resume uploaded for {candidate['email']}",
        "resume":   resume_record
    }


@router.get("/{drive_id}/candidates/{candidate_id}/view")
def view_resume(
    drive_id: str,
    candidate_id: str,
    hr=Depends(get_current_hr)
):
    """
    Returns a signed URL HR can use to view the uploaded resume.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    resume = get_resume_by_candidate(candidate_id)
    if not resume:
        raise HTTPException(
            status_code=404, detail="No resume found"
        )

    signed_url = get_resume_signed_url(resume["resume_url"])
    if not signed_url:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate view link"
        )

    return {"url": signed_url}


@router.delete("/{drive_id}/candidates/{candidate_id}")
def delete_resume(
    drive_id: str,
    candidate_id: str,
    hr=Depends(get_current_hr)
):
    """
    Delete a resume — used if HR wants to re-upload
    a different file.
    """
    drive = get_drive_by_id(drive_id)
    print("Drive HR ID:", drive["hr_id"])
    print("Logged in HR ID:", hr["id"])
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    resume = get_resume_by_candidate(candidate_id)
    if not resume:
        raise HTTPException(
            status_code=404, detail="No resume found"
        )

    delete_resume_file(resume["resume_url"])

    supabase_delete = (
        get_resume_by_candidate(candidate_id)
    )
    # Clear the record fields but keep the row for tracking
    from database.client import supabase
    supabase.table("resume_match").update({
        "resume_url":        None,
        "extracted_skills":  None,
        "match_percentage":  None,
        "passed":            False
    }).eq("candidate_id", candidate_id).execute()

    return {"message": "Resume deleted"}

@router.post("/{drive_id}/parse-all")
def parse_all_resumes(drive_id: str, hr=Depends(get_current_hr)):
    """
    Parse all unparsed resumes for a drive.
    Called when HR clicks "Proceed to Matching".
    This may take 10-30 seconds depending on resume count.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    result = parse_all_resumes_for_drive(drive_id)
    return result


@router.post("/{drive_id}/candidates/{candidate_id}/parse")
def parse_single_resume(
    drive_id: str,
    candidate_id: str,
    hr=Depends(get_current_hr)
):
    """
    Parse or re-parse a single candidate's resume.
    Useful for retrying a failed parse.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    result = parse_resume(candidate_id)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


@router.get("/{drive_id}/candidates/{candidate_id}/extracted")
def get_extracted_data(
    drive_id: str,
    candidate_id: str,
    hr=Depends(get_current_hr)
):
    """
    View the extracted resume data for a candidate.
    Useful for HR to sanity-check what OpenAI pulled out.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    data = get_extracted_skills(candidate_id)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No extracted data found. Resume may not "
                   "be parsed yet."
        )

    return data