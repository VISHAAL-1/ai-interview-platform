import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from . import crud, auth, schemas, models 
from .websocket_manager import manager
from .ai_evaluator import evaluate_answer_with_gemini
from .config import settings
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List
import traceback

app = FastAPI(title="AI Interviewer")

# --- CORS MIDDLEWARE FIX ---
origins = [
    "http://localhost:5173", # Frontend URL
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
async def startup():
    # This runs the table creation
    await init_db()

# Dependency for authentication (Unchanged)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub"))
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- Auth Endpoints ---

@app.post("/register", response_model=schemas.UserOut)
async def register(u: schemas.UserCreate):
    existing = await crud.get_user_by_email(u.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered. Please sign in.")
    
    try:
        user = await crud.create_user(u.email, u.password, u.full_name)
        return user
    except Exception:
        # Log error locally and provide generic frontend response
        print("--- CRITICAL REGISTRATION ERROR TRACE ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Registration failed due to server error.")

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await crud.get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    from .auth import verify_password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Store user.id in the 'sub' claim of the JWT
    access_token = auth.create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# --- Interview Logic Endpoints ---

@app.post("/start_interview", response_model=schemas.InterviewOut)
async def start_interview(payload: schemas.InterviewCreate, current_user = Depends(get_current_user)):
    if payload.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Unauthorized ID for interview start")
         
    it = await crud.create_interview(payload.user_id)
    return it

@app.get("/questions", response_model=List[schemas.QuestionOut])
async def get_questions(
    level: int = 1, 
    limit: int = 5, 
    current_user = Depends(get_current_user)
):
    questions = await crud.list_questions(level=level, limit=limit)
    return questions

@app.get("/profile/stats", response_model=schemas.ProfileStatsOut)
async def get_profile_stats(current_user = Depends(get_current_user)):
    stats = await crud.get_user_interview_stats(current_user.id)
    return stats

# --- WebSocket Endpoint (Unchanged) ---

from fastapi import WebSocket, WebSocketDisconnect
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = None):
    # Simplified logic, assuming token is valid
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "transcript":
                question = data.get("question", "unknown")
                answer_text = data.get("text", "")
                
                eval_res = await evaluate_answer_with_gemini(question, answer_text) # <-- NEW FUNCTION CALL
                await manager.broadcast(room_id, {"type":"evaluation","evaluation":eval_res})
            else:
                await manager.broadcast(room_id, data)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)