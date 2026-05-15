from fastapi import APIRouter

from services.openai_service import (
    generate_and_store_questions
)

from services.question_service import (
    get_questions
)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


@router.post("/generate")
def generate(
    role: str,
    segment: str,
    experience_band: str
):

    result = generate_and_store_questions(
        role,
        segment,
        experience_band
    )

    return result


@router.get("/fetch")
def fetch(
    role: str,
    segment: str,
    experience_band: str
):

    questions = get_questions(
        role,
        segment,
        experience_band
    )

    return {
        "count": len(questions),
        "questions": questions
    }