from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)
from routes.auth import (
    router as auth_router
)
from routes.questions import (
    router as questions_router
)
from routes.drives import (
    router as drive_router
)
from routes.exam import (
    router as exam_router
)
from routes.results import (
    router as results_router
)
from routes.candidate_auth import (
    router as candidate_auth_router
)
from routes.scoring import router as scoring_router

app = FastAPI()


app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.include_router(
    auth_router
)
app.include_router(
    questions_router
)
app.include_router(
    drive_router
)
app.include_router(
    exam_router
)
app.include_router(
    results_router
)
app.include_router(
    candidate_auth_router
)
app.include_router(scoring_router)
@app.get("/")
def home():

    return {
        "message":
            "Backend Running"
    }