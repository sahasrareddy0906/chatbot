# AI Recruitment System

## Project Overview

AI-powered recruitment platform that:

* Creates hiring drives
* Generates AI-based interview questions
* Conducts candidate assessments
* Scores candidates automatically
* Allows HR shortlisting

---

## Tech Stack

### Backend

* FastAPI
* Supabase
* OpenAI API
* Python

### Frontend

* React
* Vite
* Axios

### Database

* Supabase PostgreSQL

---

## Backend Structure

### routes/questions.py

Endpoints:

* `POST /questions/generate` - Generate and store questions for a role/segment/band
* `GET /questions/fetch` - Retrieve all questions for a combination
* `GET /questions/preview` - Get random sample (default 5) of questions
* `GET /questions/coverage` - Audit question bank coverage and get summary statistics

---

### routes/exam.py

Responsibilities:

* Start exam
* Resume or continue an existing exam
* Save answer
* Submit exam
* Get results
* Report time remaining for the active session
* Auto-submit expired sessions

Uses:

* services/exam_service.py

---

### services/exam_service.py

Responsibilities:

* Create exam sessions
* Resume existing exams
* Assign questions
* Save candidate answers
* Calculate scores
* Store results
* Track exam expiry and time remaining
* Auto-submit sessions when time expires

Depends On:

* candidate_service.py
* question_service.py

---

### services/question_service.py

Responsibilities:

* Insert questions
* Fetch questions
* Count questions

Database Table:

* question

---

### services/openai_service.py

Responsibilities:

* Generate AI questions
* Role-based questions
* Experience-based difficulty
* Management scenario question generation for 5+ years candidates

Additional Notes:

* New script: `scripts/populate_management.py` fills the management question bank using `POST /questions/generate`.

---

### services/question_coverage_service.py

Responsibilities:

* Audit question bank coverage
* Identify missing combinations
* Track completion status

Key Functions:

* `get_question_coverage()` - Returns all role/segment/band combinations with question counts
* `find_missing_combinations()` - Identifies combinations below 30 questions
* `get_coverage_summary()` - Aggregated statistics (total roles, combinations, complete/incomplete count)

Used By:

* `GET /questions/coverage` endpoint
* `scripts/populate_missing_questions.py` auto-population script

---

### services/candidate_service.py

Responsibilities:

* Candidate information
* Experience band management
* Drive mapping

---

## Frontend Structure

### ExamStart.jsx

Purpose:

* Start or resume exam

API Calls:

* api.startExam()

---

### ExamPage.jsx

Purpose:

* Display questions
* Save answers
* Submit exam
* Show live countdown, warning states, and auto-submit on expiry
* Protect against accidental refresh or tab loss during the exam

API Calls:

* api.saveAnswer()
* api.submitExam()
* api.getTimeRemaining()
* api.forceSubmitExpired()

---

### ResultsPage.jsx

Purpose:

* Display exam results
* HR shortlisting

API Calls:

* api.getExamResults()

---

### api.js

Purpose:

* Central API service
* All frontend-backend communication
* Handles timer sync, answer persistence, submission, and expiry endpoints

---

## Database Tables

### hiring_drive

Stores hiring drive information.

### candidate

Stores candidate information.

### question

Stores generated questions.

### exam_session

Stores exam sessions.

### exam_question

Stores assigned questions and answers.

### exam_result

Stores candidate scores and shortlist status.

---

## Business Rules

### Experience Bands

#### 0-2 Years

Segments:

* Technical
* Analytical

Expected Questions:

* 20

---

#### 2-5 Years

Segments:

* Technical
* Analytical
* Domain

Expected Questions:

* 30

---

#### 5+ Years

Segments:

* Technical
* Analytical
* Domain
* Management

Expected Questions:

* 40

---

### Questions Per Segment

10

### Exam Duration

60 Minutes

---

## Important Dependencies

If exam_session changes:

* exam_service.py
* ExamStart.jsx
* ExamPage.jsx

If question schema changes:

* openai_service.py
* question_service.py
* exam_service.py

If API endpoint changes:

* api.js
* corresponding React page

If experience band logic changes:

* candidate_service.py
* exam_service.py
* openai_service.py

---

## Current Status

Completed:

* Candidate Login
* Experience Band Selection
* AI Question Generation
* Exam Creation
* Exam Submission
* Score Calculation
* Results Dashboard
* Live exam timer and countdown warnings
* Auto-submit on exam expiry
* Timeout messaging on the results page

In Progress:

* HR Shortlisting
* Advanced Analytics
