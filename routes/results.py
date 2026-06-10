from fastapi import APIRouter

from database.client import (
    supabase
)


router = APIRouter(

    prefix="/results",

    tags=["Results"]
)


# =========================
# GET ALL RESULTS
# =========================

@router.get("/")
def get_results():

    response = (

        supabase.table(
            "exam_result"
        )

        .select("*")

        .execute()
    )

    return {

        "results":
            response.data
    }