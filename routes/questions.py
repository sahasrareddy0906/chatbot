from fastapi import APIRouter
from services.question_service import save_questions
from services.openai_service import (
    generate_questions
)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)

@router.get("/generate")
def generate(
    skill: str,
    segment: str,
    experience_band: str,
    count: int = 3
):

    questions = generate_questions(
        skill,
        segment,
        experience_band,
        count
    )

    saved = save_questions(
        questions,
        skill,
        segment,
        experience_band
    )

    return {
        "generated": len(questions),
        "saved": len(saved),
        "questions": saved
    }