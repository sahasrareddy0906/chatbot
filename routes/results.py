from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.results_service import (
    get_ranked_results,
    get_drive_stats,
    shortlist_candidates,
    unshortlist_candidates
)
from services.drive_service import get_drive_by_id
from dependencies.auth import get_current_hr

router = APIRouter(prefix="/results", tags=["Results"])


class ShortlistRequest(BaseModel):
    result_ids: list[str]


@router.get("/{drive_id}")
def get_results(drive_id: str, hr=Depends(get_current_hr)):
    """
    Full ranked results for a drive.
    HR dashboard's main results table.
    """
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    results = get_ranked_results(drive_id)
    stats   = get_drive_stats(drive_id)

    return {
        "results": results,
        "stats":   stats
    }


@router.get("/{drive_id}/stats")
def get_stats(drive_id: str, hr=Depends(get_current_hr)):
    """Quick stats only — for dashboard summary cards."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    return get_drive_stats(drive_id)


@router.post("/{drive_id}/shortlist")
def shortlist(
    drive_id: str,
    request: ShortlistRequest,
    hr=Depends(get_current_hr)
):
    """HR selects candidates to move forward."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    if not request.result_ids:
        raise HTTPException(
            status_code=400,
            detail="No candidates selected"
        )

    result = shortlist_candidates(request.result_ids)
    return result


@router.post("/{drive_id}/unshortlist")
def unshortlist(
    drive_id: str,
    request: ShortlistRequest,
    hr=Depends(get_current_hr)
):
    """HR reverses a shortlist decision."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    if drive["hr_id"] != hr["id"]:
        raise HTTPException(status_code=403, detail="Not your drive")

    result = unshortlist_candidates(request.result_ids)
    return result