import os
from database.client import supabase

BUCKET_NAME = "resume"
SIGNED_URL_EXPIRY = 3600 * 24 * 7  # 7 days


def upload_resume_file(candidate_id: str, drive_id: str,
                       file_bytes: bytes,
                       original_filename: str) -> dict | None:
    """
    Upload a resume PDF to Supabase Storage.
    Path structure: {drive_id}/{candidate_id}/{filename}
    This keeps resumes organised per drive per candidate.
    """
    # Sanitise filename — keep extension, strip risky characters
    ext = original_filename.split(".")[-1].lower()
    if ext not in ["pdf", "doc", "docx"]:
        return {"error": "Invalid file type. Use PDF, DOC, or DOCX."}

    safe_filename = f"resume.{ext}"
    storage_path = f"{drive_id}/{candidate_id}/{safe_filename}"

    try:
        # Upload — upsert=True allows overwriting if HR re-uploads
        result = supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": _get_content_type(ext),
                "upsert": "true"
            }
        )

        return {
            "success":      True,
            "storage_path": storage_path,
            "filename":     original_filename
        }

    except Exception as e:
        print(f"❌ Resume upload failed: {e}")
        return {"error": str(e)}


def get_resume_signed_url(storage_path: str) -> str | None:
    """
    Generate a temporary signed URL to view/download a resume.
    URL expires after SIGNED_URL_EXPIRY seconds.
    """
    try:
        result = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=storage_path,
            expires_in=SIGNED_URL_EXPIRY
        )
        return result.get("signedURL") or result.get("signed_url")
    except Exception as e:
        print(f"❌ Failed to generate signed URL: {e}")
        return None


def delete_resume_file(storage_path: str) -> bool:
    """Delete a resume file — used if HR wants to re-upload."""
    try:
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        return True
    except Exception as e:
        print(f"❌ Failed to delete resume: {e}")
        return False


def download_resume_bytes(storage_path: str) -> bytes | None:
    """
    Download raw file bytes — used by OpenAI parser tomorrow
    to extract text from the resume.
    """
    try:
        result = supabase.storage.from_(BUCKET_NAME).download(
            storage_path
        )
        return result
    except Exception as e:
        print(f"❌ Failed to download resume: {e}")
        return None


def _get_content_type(ext: str) -> str:
    mapping = {
        "pdf":  "application/pdf",
        "doc":  "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument"
               ".wordprocessingml.document"
    }
    return mapping.get(ext, "application/octet-stream")