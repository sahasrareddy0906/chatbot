# AI Recruitment Backend

This backend uses FastAPI, Supabase, and OpenAI to generate and serve recruitment exam questions.

## Features

### Question Generation

* Management question generation is supported for `5+` experience band candidates.
* Questions are randomized (options A-D shuffled with correct_answer mapping updated).
* Use `backend/scripts/populate_management.py` to populate the management question bank for senior roles.

### Question Bank Audit

* `GET /questions/coverage` endpoint provides real-time coverage statistics.
* Track completion status: total combinations, complete, incomplete, and total questions.
* `backend/scripts/populate_missing_questions.py` auto-populates gaps automatically.

### Candidate Exam Flow

* The exam session now exposes time remaining information for the active candidate.
* Countdown warnings appear at low and critical time thresholds.
* Expired sessions are auto-submitted and routed to the results page with a timeout message.
* Refresh and tab-loss protection is included during the active exam attempt.

## Scripts

### populate_management.py

Populates management questions for all 10 senior roles:
```bash
python backend/scripts/populate_management.py
```

### populate_missing_questions.py

Audits question bank and auto-fills gaps to meet 30-question minimum per combination:
```bash
python backend/scripts/populate_missing_questions.py
```

Provides detailed output:
- Role, Segment, Band, Existing count, Generated count, Final count
- Summary statistics (processed, successful, failed, total generated)
- Final coverage report with completion percentage
