from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from datetime import timedelta

from .config import settings
from . import crud, auth, schemas
from .db import init_db
from .websocket_manager import manager
from .audio_processor import process_audio_and_evaluate


# ----------------------------
# INIT APP
# ----------------------------
app = FastAPI(title="AI Interviewer")

# ----------------------------
# CORS - ONLY THIS BLOCK
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # 🔥 Correct
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ----------------------------
# STARTUP INIT
# ----------------------------
@app.on_event("startup")
async def startup():
    await init_db()


# ---------------- AUTH ----------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    user_id = int(payload.get("sub"))
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    return user


@app.post("/register", response_model=schemas.UserOut)
async def register(u: schemas.UserCreate):
    existing = await crud.get_user_by_email(u.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = await crud.create_user(u.email, u.password, u.full_name)
    return user


@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await crud.get_user_by_email(form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(400, "Incorrect username or password")

    token = auth.create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


# ---------------- INTERVIEW ----------------
@app.post("/start_interview", response_model=schemas.InterviewOut)
async def start_interview(payload: schemas.InterviewCreate, current_user=Depends(get_current_user)):
    if payload.user_id != current_user.id:
        raise HTTPException(403, "Unauthorized interview start")

    interview = await crud.create_interview(payload.user_id)
    return interview


@app.get("/questions", response_model=list[schemas.QuestionOut])
async def get_questions(level: int = 1, limit: int = 5, current_user=Depends(get_current_user)):
    return await crud.list_questions(level, limit)


@app.get("/profile/stats")
async def get_profile_stats(current_user=Depends(get_current_user)):
    return await crud.get_user_interview_stats(current_user.id)


# ---------------- WEBSOCKET ----------------
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = None):
    await manager.connect(room_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "audio_data":
                await process_audio_and_evaluate(
                    room_id=room_id,
                    question=data.get("question"),
                    interview_id=data.get("interview_id"),
                    base64_audio=data.get("data"),
                    manager=manager
                )
            else:
                await manager.broadcast(room_id, data)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
