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
    """Returns summary + full evaluation history for Profile page."""
    async with async_session() as session:

        # --- Summary ---
        q_summary = await session.execute(
            select(
                func.count(Evaluation.id),
                func.avg(Evaluation.correctness_score),
                func.avg(Evaluation.fluency_score),
                func.avg(Evaluation.combined_score),
            ).join(Interview, Evaluation.interview_id == Interview.id)
            .where(Interview.user_id == user_id)
        )
        summary = q_summary.one_or_none()
        total_interviews = summary[0] or 0
        avg_correctness = float(summary[1] or 0)
        avg_fluency = float(summary[2] or 0)
        avg_combined = float(summary[3] or 0)

        # --- Last Feedback ---
        q_latest_feedback = await session.execute(
            select(Evaluation.feedback)
            .join(Interview, Evaluation.interview_id == Interview.id)
            .where(Interview.user_id == user_id)
            .order_by(Evaluation.created_at.desc())
            .limit(1)
        )
        last_feedback = q_latest_feedback.scalars().first() or "No interviews yet."

        # --- Full History ---
        q_history = await session.execute(
            select(Evaluation)
            .join(Interview, Evaluation.interview_id == Interview.id)
            .where(Interview.user_id == user_id)
            .order_by(Evaluation.created_at.desc())
        )
        history = q_history.scalars().all()

        return {
            "total_interviews": total_interviews,
            "avg_correctness": avg_correctness,
            "avg_fluency": avg_fluency,
            "avg_combined": avg_combined,
            "last_feedback": last_feedback,
            "history": history,
        }


from .models import Evaluation

async def save_evaluation(interview_id: int, question_text: str, eval_data: dict):
    async with async_session() as session:
        evaluation = Evaluation(
            interview_id=interview_id,
            question_text=question_text,
            correctness_score=eval_data["correctness_score"],
            fluency_score=eval_data["fluency_score"],
            combined_score=eval_data["combined_score"],
            feedback=eval_data["feedback"],
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)
        return evaluation
