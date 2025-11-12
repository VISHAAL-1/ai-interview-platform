from google.cloud import speech
from google.oauth2 import service_account
import os

def transcribe_audio_google(wav_path: str):
    """
    Basic synchronous speech-to-text using Google Cloud Speech.
    User must set GOOGLE_APPLICATION_CREDENTIALS env var or pass creds path.
    """
    client = speech.SpeechClient()
    with open(wav_path, "rb") as f:
        audio = speech.RecognitionAudio(content=f.read())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    response = client.recognize(config=config, audio=audio)
    transcripts = []
    for result in response.results:
        transcripts.append(result.alternatives[0].transcript)
    return " ".join(transcripts)
