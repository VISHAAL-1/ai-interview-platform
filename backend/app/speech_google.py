from google.cloud import speech
from google.oauth2 import service_account
from .config import settings
import os

def transcribe_audio_google(wav_path: str):
    """
    Transcribes WAV audio using Google Cloud Speech-to-Text
    with EXPLICIT credentials (works reliably in FastAPI).
    """

    # Load the JSON file path from your .env
    creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS

    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(f"Google STT credentials not found at: {creds_path}")

    # Load credentials explicitly
    credentials = service_account.Credentials.from_service_account_file(creds_path)

    client = speech.SpeechClient(credentials=credentials)

    with open(wav_path, "rb") as f:
        audio = speech.RecognitionAudio(content=f.read())

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)

    transcripts = [result.alternatives[0].transcript for result in response.results]
    return " ".join(transcripts)
