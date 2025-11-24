import asyncio
import json
import re
from google import genai
from google.genai import types
from .config import settings

# ---- REQUIRED GLOBAL CLIENT ----
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def evaluate_answer_with_gemini(question_text, answer_text, acoustic_features):
    """
    Evaluate correctness using transcript + fluency using acoustic features.
    """

    prompt = f"""
    Evaluate a candidate's interview answer.

    You MUST return a JSON object with ONLY these keys:
    - correctness_score (0–100)
    - fluency_score (0–100)
    - combined_score (0–100)
    - feedback (string)

    --- Interview Question ---
    {question_text}

    --- Transcript ---
    "{answer_text}"

    --- Acoustic Features (from real audio analysis) ---
    jitter: {acoustic_features['jitter']}          # vocal stability
    shimmer: {acoustic_features['shimmer']}        # amplitude stability
    loudness: {acoustic_features['loudness']}      # speaking energy
    speech_rate: {acoustic_features['speech_rate']}  # words per second
    pause_ratio: {acoustic_features['pause_ratio']}  # silence proportion

    **Interpretation rules for fluency:**
    - High jitter/shimmer = shaky/unclear voice → reduce fluency score
    - Very low or very high speech rate = slow/rushed speech → reduce fluency score
    - High pause_ratio = too many pauses → reduce fluency
    - loudness too low = low confidence

    Rate correctness ONLY on meaning and quality of the transcript.
    """

    loop = asyncio.get_event_loop()

    def run_gemini():
        return client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

    resp = await loop.run_in_executor(None, run_gemini)
    content = resp.text

    try:
        return json.loads(content)
    except:
        import re
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            return json.loads(match.group(0))
        return {
            "correctness_score": 0,
            "fluency_score": 0,
            "combined_score": 0,
            "feedback": "Could not parse Gemini response."
        }
async def generate_followup_question(transcript: str):
    prompt = f"""
    You are an AI interviewer.
    Given the candidate's answer, generate ONE follow-up question.
    Make it relevant and non-repetitive.

    Answer: {transcript}

    Output ONLY the follow-up question as plain text.
    """

    loop = asyncio.get_event_loop()

    def run_gemini():
        return client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

    resp = await loop.run_in_executor(None, run_gemini)
    return resp.text.strip()
