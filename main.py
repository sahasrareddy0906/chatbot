from fastapi import FastAPI
from routes.candidates import router as candidate_router

app = FastAPI()

app.include_router(candidate_router)

@app.get("/")
def root():
    return {"message": "Backend running"}