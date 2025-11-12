from sqlalchemy.future import select
from sqlalchemy import insert, func
from .models import User, Interview, Question
from .db import async_session
from .auth import hash_password
from sqlalchemy.exc import NoResultFound

async def create_user(email: str, password: str, full_name: str = None):
    # Debugging print removed from here to rely on main.py's traceback
    async with async_session() as session:
        # Note: full_name=None is acceptable if models.User is set to nullable=True
        user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
        session.add(user)
        await session.commit() # This line is the potential commit failure point
        await session.refresh(user)
        return user

async def get_user_by_email(email: str):
    async with async_session() as session:
        q = await session.execute(select(User).where(User.email == email))
        return q.scalars().first()

async def get_user(user_id: int):
    async with async_session() as session:
        q = await session.execute(select(User).where(User.id == user_id))
        return q.scalars().first()

async def create_interview(user_id: int):
    async with async_session() as session:
        it = Interview(user_id=user_id)
        session.add(it)
        await session.commit()
        await session.refresh(it)
        return it

async def update_interview_feedback(interview_id: int, score: float, feedback: str):
    async with async_session() as session:
        q = await session.execute(select(Interview).where(Interview.id == interview_id))
        it = q.scalars().first()
        if it:
            it.score = score
            it.feedback = feedback
            await session.commit()
            await session.refresh(it)
        return it

async def list_questions(level: int = 1, limit: int = 10):
    async with async_session() as session:
        q = await session.execute(select(Question).where(Question.level == level).limit(limit))
        questions = q.scalars().all()
        
        # Temporary fallback questions for testing
        if not questions:
            return [
                Question(id=1, text="Explain the difference between a process and a thread.", level=1),
                Question(id=2, text="Describe how the virtual DOM works in React.", level=1),
                Question(id=3, text="What is a closure in JavaScript, and provide a use case?", level=1),
                Question(id=4, text="Walk me through the steps of an HTTP GET request.", level=1),
            ]
        return questions

async def get_user_interview_stats(user_id: int):
    """Calculates and returns interview statistics for the Profile page."""
    async with async_session() as session:
        q_stats = await session.execute(
            select(
                func.count(Interview.id).label('total_interviews'),
                func.avg(Interview.score).label('avg_score')
            ).where(Interview.user_id == user_id)
        )
        stats = q_stats.one_or_none()

        total_interviews = stats.total_interviews if stats else 0
        avg_score = float(stats.avg_score) if stats and stats.avg_score is not None else 0.0

        q_latest = await session.execute(
            select(Interview.feedback)
            .where(Interview.user_id == user_id)
            .where(Interview.feedback != None) 
            .order_by(Interview.id.desc())
            .limit(1)
        )
        latest_feedback = q_latest.scalars().first()
        
        return {
            "total_interviews": total_interviews,
            "avg_score": avg_score,
            "last_feedback": latest_feedback if latest_feedback else "No interviews completed yet."
        }