from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InterviewCreate(BaseModel):
    user_id: int

class InterviewOut(BaseModel):
    id: int
    user_id: int
    score: Optional[float]
    feedback: Optional[str]
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime]
    class Config:
        orm_mode = True

# NEW SCHEMA
class QuestionOut(BaseModel):
    id: int
    text: str
    level: int
    tags: Optional[str]

    class Config:
        orm_mode = True
        
# NEW SCHEMA
class ProfileStatsOut(BaseModel):
    total_interviews: int
    avg_score: float
    last_feedback: str