import os
import json
import re
from google import genai
from google.genai import types
from .config import settings

# Initialize the Gemini Client instance
# It automatically reads the GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.
# We explicitly pass the key here for consistency with your previous structure.
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def evaluate_answer_with_gemini(question_text: str, answer_text: str) -> dict:
    """
    Sends a prompt to Gemini (or other LLM) to evaluate correctness, fluency, scoring, and suggestions.
    Returns dict with score (0-100) and feedback text.
    """
    prompt = f"""
    You are an interviewer evaluator. Given the interview question and the candidate's answer, provide:
    1) A score 0-100 for correctness/technical content.
    2) A score 0-100 for communication/fluency.
    3) A short feedback paragraph with 3 improvement points.
    
    You MUST return the output as a single JSON object.
    JSON keys MUST be: correctness_score (number), fluency_score (number), combined_score (number), feedback (string).
    
    ---
    Question: {question_text}
    Answer: {answer_text}
    """
    try:
        resp = client.models.generate_content(
            # --- FIX: SWITCHING TO A DIFFERENT FLASH MODEL ---
            model='models/gemini-2.5-flash', # Try with explicit models/ prefix 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        
        # The content should be a JSON string due to response_mime_type="application/json"
        content = resp.text
        
        # Attempt to parse the content as JSON directly
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback for imperfect JSON
            match = re.search(r'\{.*\}', content, re.S)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            
            # Final fallback: return raw content in feedback
            return {"correctness_score": 70.0, "fluency_score": 75.0, "combined_score": 72.5, "feedback": content}
            
    except Exception as e:
        # If the API call itself fails (e.g., bad key, network issue)
        return {"correctness_score": 0.0, "fluency_score": 0.0, "combined_score": 0.0, "feedback": f"LLM API error (Gemini): {e}"}