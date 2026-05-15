import os
import json

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


DIFFICULTY_MAP = {
    "0-2": {
        "label": "beginner",
        "description": "Basic syntax and simple concepts."
    },

    "2-5": {
        "label": "intermediate",
        "description": "Moderate problem solving and practical usage."
    },

    "5+": {
        "label": "advanced",
        "description": "Deep concepts and architecture."
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


def build_prompt(
    skill,
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
Generate exactly {count} MCQ questions.

Skill: {skill}

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
    skill,
    segment,
    experience_band,
    count=3
):

    prompt = build_prompt(
        skill,
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
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):

            raw = raw.split("```")[1]

            if raw.startswith("json"):
                raw = raw[4:]

        raw = raw.strip()

        questions = json.loads(raw)

        return questions

    except Exception as e:

        return {
            "error": str(e)
        }