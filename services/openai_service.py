import os
import json

from openai import OpenAI
from dotenv import load_dotenv

from services.question_service import (
    insert_questions,
    count_questions
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


DIFFICULTY_MAP = {
    "0-2": {
        "label": "beginner",
        "description":
            "Basic syntax, definitions, simple concepts."
    },

    "2-5": {
        "label": "intermediate",
        "description":
            "Practical application and moderate problem solving."
    },

    "5+": {
        "label": "advanced",
        "description":
            "Deep concepts, architecture, scalability and performance."
    }
}


SEGMENT_MAP = {
    "technical":
        "Technical coding and implementation knowledge.",

    "analytical":
        "Logical reasoning and analytical thinking.",

    "domain":
        "Industry-specific domain knowledge.",

    "management":
        "Leadership and management scenarios."
}


MIN_QUESTIONS_PER_COMBO = 30


def build_prompt(
    role,
    segment,
    experience_band,
    count
):

    difficulty = DIFFICULTY_MAP.get(
        experience_band,
        DIFFICULTY_MAP["0-2"]
    )

    seg_desc = SEGMENT_MAP.get(segment, "")

    prompt = f"""
You are an exam question generator for a technical recruitment system.

Generate exactly {count} MCQ questions.

Role: {role}

Segment:
{segment} — {seg_desc}

Experience band:
{experience_band}

Difficulty:
{difficulty['label']} —
{difficulty['description']}

Rules:
1. Exactly 4 options
2. correct_answer must be A/B/C/D
3. Return ONLY JSON array
4. No markdown
5. No explanations
6. Questions must be unique

Format:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A"
  }}
]
"""

    return prompt


def generate_questions(
    role,
    segment,
    experience_band,
    count=10
):

    prompt = build_prompt(
        role,
        segment,
        experience_band,
        count
    )

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",

            messages=[
                {
                    "role": "system",
                    "content":
                        "You are a strict JSON-only generator."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7,
            max_tokens=3000
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):

            raw = raw.split("```")[1]

            if raw.startswith("json"):
                raw = raw[4:]

        raw = raw.strip()

        questions = json.loads(raw)

        for q in questions:

            required = [
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_answer"
            ]

            for field in required:

                if field not in q:
                    raise ValueError(
                        f"Missing field: {field}"
                    )

        return questions

    except json.JSONDecodeError as e:

        print(f"JSON parse error: {e}")

        return []

    except Exception as e:

        print(f"OpenAI error: {e}")

        return []


def generate_and_store_questions(
    role,
    segment,
    experience_band,
    count=10
):

    existing = count_questions(
        role,
        segment,
        experience_band
    )

    if existing >= MIN_QUESTIONS_PER_COMBO:

        return {
            "status": "skipped",
            "existing_count": existing,
            "new_count": 0
        }

    questions = generate_questions(
        role,
        segment,
        experience_band,
        count
    )

    if not questions:

        return {
            "status": "failed"
        }

    stored = insert_questions(
        questions,
        role,
        segment,
        experience_band
    )

    return {
        "status": "success",
        "existing_count": existing,
        "new_count": len(stored),
        "total_count": existing + len(stored)
    }