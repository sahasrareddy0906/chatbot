import random

from datetime import (
    datetime,
    timedelta,
    timezone
)

from database.client import supabase

from services.candidate_service import (
    get_segments_for_band
)

from services.question_service import (
    get_questions
)


QUESTIONS_PER_SEGMENT = 10

EXAM_DURATION_MINUTES = 60


# =========================
# EXISTING SESSION
# =========================

def get_existing_session(
    candidate_id: str
):

    response = (
        supabase.table("exam_session")
        .select("*")
        .eq("candidate_id", candidate_id)
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


# =========================
# CREATE SESSION
# =========================

def create_exam_session(
    candidate_id: str,
    drive_id: str
):

    now = datetime.now(
        timezone.utc
    )

    expiry = (
        now +
        timedelta(
            minutes=
            EXAM_DURATION_MINUTES
        )
    )

    response = (
        supabase.table("exam_session")
        .insert({
            "candidate_id": candidate_id,
            "start_time": now.isoformat(),
            "end_time": expiry.isoformat(),
            "submitted": False,
            "proctoring_status": "active"
        })
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


# =========================
# RANDOM QUESTIONS
# =========================

def pick_random_questions(
    role: str,
    segment: str,
    experience_band: str,
    count: int = QUESTIONS_PER_SEGMENT
):

    all_questions = get_questions(
        role,
        segment,
        experience_band
    )

    if not all_questions:
        return []

    if len(all_questions) <= count:
        return all_questions
    print("ROLE IN PICK:", role)
    print("SEGMENT IN PICK:", segment)
    return random.sample(
        all_questions,
        count
    )


# =========================
# ASSIGN QUESTIONS
# =========================

def assign_questions_to_session(
    session_id: str,
    questions: list
):

    rows = []

    for idx, q in enumerate(
        questions
    ):

        rows.append({
            "session_id": session_id,
            "question_id": q["id"],
            "candidate_answer": None,
            "is_correct": None
        })

    if not rows:
        return False

    response = (
        supabase.table("exam_question")
        .insert(rows)
        .execute()
    )

    return bool(response.data)


# =========================
# TIME REMAINING
# =========================

def calculate_time_remaining(
    end_time_str: str
):

    end_time = datetime.fromisoformat(
        end_time_str
    )

    if end_time.tzinfo is not None:

        end_time = end_time.replace(
            tzinfo=None
        )

    now = datetime.utcnow()

    remaining = (
        end_time - now
    ).total_seconds()

    return max(
        0,
        int(remaining)
    )


def is_session_expired(
    session: dict
) -> bool:

    end_time_str = session.get(
        "end_time"
    )

    if not end_time_str:
        return False

    normalized = end_time_str.replace(
        "Z",
        "+00:00"
    )

    end_time = datetime.fromisoformat(
        normalized
    )

    if end_time.tzinfo is None:
        end_time = end_time.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    return now >= end_time


def get_time_remaining_seconds(
    session: dict
) -> int:

    end_time_str = session.get(
        "end_time"
    )

    if not end_time_str:
        return 0

    normalized = end_time_str.replace(
        "Z",
        "+00:00"
    )

    end_time = datetime.fromisoformat(
        normalized
    )

    if end_time.tzinfo is None:
        end_time = end_time.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    remaining = (
        end_time - now
    ).total_seconds()

    return max(0, int(remaining))


def auto_submit_expired_sessions():

    now = datetime.now(
        timezone.utc
    ).isoformat()

    response = (
        supabase.table("exam_session")
        .select("id, candidate_id")
        .eq("submitted", False)
        .lt("end_time", now)
        .execute()
    )

    submitted_ids = []

    for session in response.data or []:
        submission = submit_exam(
            session["id"],
            session["candidate_id"]
        )

        if submission.get("score") is not None or submission.get("error") != "already_submitted":
            submitted_ids.append(
                session["id"]
            )

    return submitted_ids


# =========================
# BUILD RESPONSE
# =========================

def build_exam_response(
    session: dict,
    questions: list,
    segment_map: dict
):

    indexed_questions = []

    for idx, q in enumerate(
        questions
    ):

        q["order_index"] = idx

        indexed_questions.append(q)

    return {
        "session": session,
        "questions": indexed_questions,
        "total_questions": len(indexed_questions),
        "segments": list(segment_map.keys()),
        "segment_counts": {
            seg: len(qs)
            for seg, qs
            in segment_map.items()
        },
        "time_remaining":
            EXAM_DURATION_MINUTES * 60,
        "resumed": False
    }


# =========================
# RESUME SESSION
# =========================

def resume_exam_session(
    session_id: str
):

    session_resp = (
        supabase.table("exam_session")
        .select("*")
        .eq("id", session_id)
        .execute()
    )

    if not session_resp.data:
        return None

    session = session_resp.data[0]

    eq_resp = (
    supabase.table("exam_question")
    .select("*, question(*)")
    .eq("session_id", session_id)
    .order("id")
    .execute()
)

    exam_questions = (
        eq_resp.data
        if eq_resp.data
        else []
    )

    questions = []

    for eq in exam_questions:

        q = eq["question"]

        q["exam_question_id"] = eq["id"]

        q["candidate_answer"] = (
            eq["candidate_answer"]
        )

        q["order_index"] = len(questions)

        questions.append(q)

    return {
        "session": session,
        "questions": questions,
        "total_questions": len(questions),
        "time_remaining":
            calculate_time_remaining(
                session["end_time"]
            ),
        "resumed": True
    }


# =========================
# ACTIVE SESSION
# =========================

def get_exam_session_by_candidate(
    candidate_id: str
):

    response = (
    supabase.table("exam_session")
    .select("*")
    .eq("candidate_id", candidate_id)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)

    return (
    response.data[0]
    if response.data
    else None
)


def get_exam_session_by_id(
    session_id: str
):

    response = (
        supabase.table("exam_session")
        .select("*")
        .eq("id", session_id)
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


def get_exam_progress(
    session_id: str
):

    total_resp = (
        supabase.table("exam_question")
        .select("id")
        .eq("session_id", session_id)
        .execute()
    )

    total_questions = len(total_resp.data or [])

    answered_resp = (
        supabase.table("exam_question")
        .select("id")
        .not_.is_("candidate_answer", "null")
        .eq("session_id", session_id)
        .execute()
    )

    answered_questions = len(answered_resp.data or [])

    progress_percentage = (
        int((answered_questions / total_questions) * 100)
        if total_questions else 0
    )

    return {
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "progress_percentage": progress_percentage
    }


# =========================
# START EXAM
# =========================

def start_exam(
    candidate_id: str,
    drive_id: str,
    experience_band: str,
    role: str
):

    existing = get_existing_session(
        candidate_id
    )

    if existing:

        if existing.get("submitted"):

            return {
                "error":
                    "already_submitted"
            }

        if is_session_expired(existing):
            submit_exam(
                existing["id"],
                candidate_id
            )

            return {
                "error":
                    "already_submitted"
            }

        return resume_exam_session(
            existing["id"]
        )



    segments = get_segments_for_band(
        experience_band
    )
    print("DEBUG SEGMENTS =", segments)
    

    all_questions = []

    segment_map = {}

    for segment in segments:

        print("LOOP SEGMENT =", segment)
        picked = pick_random_questions(
            role=role,
            segment=segment,
            experience_band=
                experience_band,
            count=
                QUESTIONS_PER_SEGMENT
        )


        segment_map[segment] = (
            picked
        )

        all_questions.extend(
            picked
        )

    if not all_questions:

        return {
            "error":
                "no_questions_found"
        }

    session = create_exam_session(
        candidate_id,
        drive_id
    )

    if not session:

        return {
            "error":
                "session_creation_failed"
        }

    success = assign_questions_to_session(
        session["id"],
        all_questions
    )

    if not success:

        return {
            "error":
                "question_assignment_failed"
        }

    print(
        "SEGMENTS:",
        segments
    )

    print(
        "TOTAL QUESTIONS:",
        len(all_questions)
    )

    for segment in segment_map:

        print(
            segment,
            len(segment_map[segment])
        )

    return build_exam_response(
        session,
        all_questions,
        segment_map
    )
def submit_exam(
    session_id: str,
    candidate_id: str
):

    session = get_exam_session_by_id(
        session_id
    )

    if not session or session["candidate_id"] != candidate_id:
        return {
            "error": "session_not_found"
        }

    if session.get("submitted"):
        return {
            "error": "already_submitted"
        }

    eq_resp = (
        supabase.table("exam_question")
        .select("*, question(*)")
        .eq("session_id", session_id)
        .execute()
    )

    exam_questions = (
        eq_resp.data
        if eq_resp.data
        else []
    )

    correct = 0
    attempted = 0
    technical_score = 0
    analytical_score = 0
    domain_score = 0
    management_score = 0

    for eq in exam_questions:

        question = eq["question"]
        candidate_answer = eq.get("candidate_answer")

        if candidate_answer is not None:
            attempted += 1

        is_correct = (
            candidate_answer is not None
            and candidate_answer
            ==
            question["correct_answer"]
        )

        if is_correct:
            correct += 1

            segment = (
                question["segment"]
                .lower()
            )

            if segment == "technical":
                technical_score += 1
            elif segment == "analytical":
                analytical_score += 1
            elif segment == "domain":
                domain_score += 1
            elif segment == "management":
                management_score += 1

        (
            supabase
            .table("exam_question")
            .update({
                "is_correct": is_correct
            })
            .eq("id", eq["id"])
            .execute()
        )

    percentage = (
        round(correct * 100 / len(exam_questions), 2)
        if exam_questions else 0
    )

    (
        supabase
        .table("exam_result")
        .insert({
            "session_id": session_id,
            "candidate_id": candidate_id,
            "total_score": correct,
            "technical_score": technical_score,
            "analytical_score": analytical_score,
            "domain_score": domain_score,
            "management_score": management_score,
            "hr_shortlisted": False
        })
        .execute()
    )

    now = datetime.now(timezone.utc).isoformat()

    (
        supabase
        .table("exam_session")
        .update({
            "submitted": True,
            "end_time": now
        })
        .eq("id", session_id)
        .execute()
    )

    (
        supabase
        .table("candidate")
        .update({
            "status": "exam_taken"
        })
        .eq("id", candidate_id)
        .execute()
    )

    return {
        "score": correct,
        "correct": correct,
        "attempted": attempted,
        "percentage": percentage
    }

def save_answer(
    session_id: str,
    question_id: str,
    candidate_answer: str
):

    if candidate_answer not in ["A", "B", "C", "D"]:
        return None

    session = get_exam_session_by_id(
        session_id
    )

    if not session or session.get("submitted"):
        return None

    response = (
        supabase.table("exam_question")
        .update({
            "candidate_answer":
                candidate_answer
        })
        .eq(
            "session_id",
            session_id
        )
        .eq(
            "question_id",
            question_id
        )
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


def get_answered_count(
    session_id: str
):

    response = (
        supabase.table("exam_question")
        .select("id")
        .not_.is_(
            "candidate_answer",
            "null"
        )
        .eq(
            "session_id",
            session_id
        )
        .execute()
    )

    return len(
        response.data
    )
def get_exam_result(
    session_id: str
):

    response = (
        supabase.table("exam_result")
        .select(
            "*, candidate(email, username)"
        )
        .eq("session_id", session_id)
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


def get_latest_candidate_result(
    candidate_id: str
):

    response = (
        supabase.table("exam_result")
        .select(
            "*, candidate(email, username)"
        )
        .eq("candidate_id", candidate_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )


def get_exam_results():

    response = (
        supabase.table("exam_result")
        .select(
            "*, candidate(email, username)"
        )
        .execute()
    )

    return (
        response.data
        if response.data
        else []
    )

def shortlist_candidate(
    result_id: str
):

    response = (
        supabase.table("exam_result")
        .update({
            "hr_shortlisted": True
        })
        .eq("id", result_id)
        .execute()
    )

    return (
        response.data[0]
        if response.data
        else None
    )