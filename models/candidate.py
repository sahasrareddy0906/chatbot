from pydantic import BaseModel

class CandidateCreate(BaseModel):
    drive_id: str
    email: str
    username: str
    password_hash: str
    experience_band: str
    status: str = "invited"