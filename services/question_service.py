from database.client import supabase


def insert_questions(
    questions,
    skill,
    segment,
    experience_band
):

    rows = []

    for q in questions:

        row = {
            "skill": skill,
            "segment": segment,
            "experience_band": experience_band,
            "question_text": q["question_text"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"]
        }

        rows.append(row)

    response = (
        supabase
        .table("question")
        .insert(rows)
        .execute()
    )

    print("INSERT RESPONSE:")
    print(response)

    return response.data if response.data else []


def get_questions(
    skill,
    segment,
    experience_band
):

    response = (
        supabase
        .table("question")
        .select("*")
        .eq("skill", skill)
        .eq("segment", segment)
        .eq("experience_band", experience_band)
        .execute()
    )

    return response.data if response.data else []


def count_questions(
    skill,
    segment,
    experience_band
):

    questions = get_questions(
        skill,
        segment,
        experience_band
    )

    return len(questions)