from fastapi import APIRouter
from models.candidate import CandidateCreate
from services.candidate_service import insert_candidate
from services.candidate_service import (
    insert_candidate,
    get_candidates_by_drive
)
router = APIRouter(prefix="/candidates")


@router.post("/")
def create_candidate(candidate: CandidateCreate):

    result = insert_candidate(
        candidate.drive_id,
        candidate.email,
        candidate.username,
        candidate.password_hash,
        candidate.experience_band
    )

    return {
        "message": "Candidate created",
        "data": result
    }
@router.get("/{drive_id}")
def get_candidates(drive_id: str):

    result = get_candidates_by_drive(drive_id)

    return result