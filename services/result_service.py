from database.client import (
    supabase
)


def save_exam_result(

    session_id: str,

    candidate_id: str,

    total_score: int,

    technical_score: int,

    analytical_score: int,

    domain_score: int,

    management_score: int,

    hr_shortlisted: bool
):

    response = (

        supabase.table(
            "exam_result"
        )

        .insert({

            "session_id":
                session_id,

            "candidate_id":
                candidate_id,

            "total_score":
                total_score,

            "technical_score":
                technical_score,

            "analytical_score":
                analytical_score,

            "domain_score":
                domain_score,

            "management_score":
                management_score,

            "hr_shortlisted":
                hr_shortlisted
        })

        .execute()
    )

    return response.data