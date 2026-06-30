from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException
)

from pydantic import (
    BaseModel
)
from services.question_service import (
    get_questions
)
from services.openai_service import (
    generate_and_store_questions
)
from services.question_coverage_service import (
    get_question_coverage,
    get_coverage_summary
)

import random

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
    role: str
    segment: str
    experience_band: str
    skill: Optional[str] = None
    count: int = 10
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

            request.role,

            request.segment,

            request.experience_band,

           count=request.count,

            skill=request.skill
        )
    )

    return result


@router.get("/fetch")
def fetch_questions(
    role: str,
    segment: str,
    experience_band: str
):

    questions = get_questions(
        role,
        segment,
        experience_band
    )

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions found for this combination"
        )

    return {
        "role": role,
        "segment": segment,
        "experience_band": experience_band,
        "count": len(questions),
        "questions": questions
    }


@router.get("/preview")
def preview_questions(
    role: str,
    segment: str,
    experience_band: str,
    limit: int = 5
):

    questions = get_questions(
        role,
        segment,
        experience_band
    )

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions found for this combination"
        )

    sample = random.sample(
        questions,
        min(limit, len(questions))
    )

    return {
        "role":            role,
        "segment":         segment,
        "experience_band": experience_band,
        "total_in_bank":   len(questions),
        "preview_count":   len(sample),
        "questions":       [
            {
                "question_text": q["question_text"],
                "option_a":      q["option_a"],
                "option_b":      q["option_b"],
                "option_c":      q["option_c"],
                "option_d":      q["option_d"],
                "correct_answer": q["correct_answer"]
            }
            for q in sample
        ]
    }


@router.get("/coverage")
def get_coverage():

    coverage = get_question_coverage()

    summary = get_coverage_summary()

    return {
        "coverage": coverage,
        "summary": summary
    }
