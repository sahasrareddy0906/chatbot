from fastapi import (
    APIRouter
)

from pydantic import (
    BaseModel
)
from services.question_service import (
    insert_questions
)
from services.openai_service import (
    generate_and_store_questions
)

router = APIRouter(

    prefix="/questions",

    tags=["Questions"]
)


# =========================
# REQUEST MODEL
# =========================

class GenerateQuestionRequest(
    BaseModel
):

    skill: str

    segment: str

    experience_band: str


# =========================
# GENERATE QUESTIONS
# =========================

@router.post("/generate")
def generate_questions(

    request:
    GenerateQuestionRequest
):

    result = (

        generate_and_store_questions(

            request.skill,

            request.segment,

            request.experience_band,

            count=10
        )
    )

    return result

    saved_questions = (

    insert_questions(

        questions,

        request.skill,

        request.segment,

        request.experience_band
    )
)


    return {

    "message":
        "Questions saved successfully",

    "count":
        len(saved_questions),

    "questions":
        saved_questions
}