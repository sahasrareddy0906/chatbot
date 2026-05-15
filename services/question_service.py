from database.client import supabase


def save_questions(
    questions,
    skill,
    segment,
    experience_band
):

    formatted_questions = []

    for q in questions:

        formatted_questions.append({
            "skill": skill,
            "segment": segment,
            "experience_band": experience_band,
            "question_text": q["question_text"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"]
        })

    response = (
        supabase
        .table("question")
        .insert(formatted_questions)
        .execute()
    )

    return response.data