from fastapi import FastAPI

from routes.candidates import router as candidate_router
from routes.questions import router as question_router

app = FastAPI(
    title="AI Recruitment System",
    version="1.0.0"
)

app.include_router(candidate_router)
app.include_router(question_router)


@app.get("/")
def root():
    return {
        "message": "AI Recruitment Backend Running"
    }