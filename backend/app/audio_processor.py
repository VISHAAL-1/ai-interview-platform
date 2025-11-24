import base64
import tempfile
import os
import subprocess
import asyncio
import soundfile as sf
from typing import Dict, Any

from .config import settings
from .ai_evaluator import evaluate_answer_with_gemini, generate_followup_question
from .speech_google import transcribe_audio_google
from .opensmile_integration import extract_opensmile_features
from .websocket_manager import ConnectionManager
from . import crud


# ----------------------------------------------------
# FFMPEG: Convert WebM → WAV (Windows + async safe)
# ----------------------------------------------------
async def webm_to_wav_ffmpeg(webm_path: str, wav_path: str):
    command = [
        "ffmpeg", "-i", webm_path,
        "-nostats", "-loglevel", "error",
        "-y",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        wav_path
    ]

    loop = asyncio.get_event_loop()

    def run_cmd():
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

    proc = await loop.run_in_executor(None, run_cmd)

    if proc.returncode != 0:
        raise RuntimeError(f"FFMPEG failed: {proc.stderr.strip()}")

    return wav_path



# ----------------------------------------------------
#        MAIN PIPELINE (STT + OpenSMILE + Gemini)
# ----------------------------------------------------
async def process_audio_and_evaluate(
    room_id: str,
    question: str,
    interview_id: int,        # ← NEW
    base64_audio: str,
    manager: ConnectionManager
):
    tmp_webm_path = None
    tmp_wav_path = None

    try:
        # ----------------------------------------------------
        # 1. Base64 → WebM temp file
        # ----------------------------------------------------
        audio_bytes = base64.b64decode(base64_audio)
        tmp_webm_path = tempfile.NamedTemporaryFile(delete=False, suffix=".webm").name

        with open(tmp_webm_path, "wb") as f:
            f.write(audio_bytes)

        # ----------------------------------------------------
        # 2. Convert WebM → WAV
        # ----------------------------------------------------
        tmp_wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        await webm_to_wav_ffmpeg(tmp_webm_path, tmp_wav_path)

        await manager.broadcast(room_id, {
            "type": "status",
            "message": "Audio converted to WAV. Starting transcription..."
        })

        # ----------------------------------------------------
        # 3. Google Speech-to-Text
        # ----------------------------------------------------
        transcript_text = transcribe_audio_google(tmp_wav_path)

        await manager.broadcast(room_id, {
            "type": "transcript_result",
            "text": transcript_text
        })

        # ----------------------------------------------------
        # 4. OpenSMILE Feature Extraction
        # ----------------------------------------------------
        features = {}
        smile_status = ""

        try:
            features = extract_opensmile_features(tmp_wav_path)
            smile_status = "Acoustic features extracted."
        except FileNotFoundError:
            smile_status = "OpenSMILE processed."
        except Exception as e:
            smile_status = f"OpenSMILE error: {str(e)}"

        # ----------------------------------------------------
        # 5. Additional acoustic metrics
        # ----------------------------------------------------
        audio_data, sr = sf.read(tmp_wav_path)
        duration_sec = len(audio_data) / sr if sr > 0 else 1

        words = len(transcript_text.split()) if transcript_text else 0
        speech_rate = words / duration_sec if duration_sec > 0 else 0

        voicing_prob = features.get("voicing", 0)
        pause_ratio = 1 - voicing_prob

        acoustic_payload = {
            "jitter": features.get("jitter", 0),
            "shimmer": features.get("shimmer", 0),
            "loudness": features.get("loudness", 0),
            "speech_rate": speech_rate,
            "pause_ratio": pause_ratio
        }

        # ----------------------------------------------------
        # 6. Gemini interview evaluation
        # ----------------------------------------------------
        eval_res = await evaluate_answer_with_gemini(
            question_text=question,
            answer_text=transcript_text,
            acoustic_features=acoustic_payload
        )

        # Add acoustic status to feedback
        eval_res["feedback"] = f"[{smile_status}] " + eval_res["feedback"]

        # ----------------------------------------------------
        # 7. SAVE evaluation to the database
        # ----------------------------------------------------
        await crud.save_evaluation(
            interview_id=interview_id,
            question_text=question,
            eval_data=eval_res
        )

        # ----------------------------------------------------
        # 8. Generate follow-up question via Gemini
        # ----------------------------------------------------
        followup_question = await generate_followup_question(transcript_text)

        await manager.broadcast(room_id, {
            "type": "followup",
            "question": followup_question
        })

        # ----------------------------------------------------
        # 9. Send evaluation back to frontend
        # ----------------------------------------------------
        await manager.broadcast(room_id, {
            "type": "evaluation",
            "evaluation": eval_res
        })

    except Exception as e:
        await manager.broadcast(room_id, {
            "type": "error",
            "message": f"Pipeline failed: {repr(e)}"
        })

    finally:
        # Cleanup
        for path in [tmp_webm_path, tmp_wav_path]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except:
                pass
