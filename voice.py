# voice.py
# This file handles all audio operations:
# 1. Text to Speech (TTS) - converts patient's words to audio
# 2. Speech to Text (STT) - converts agent's audio response to text

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text, output_path):
    """
    Converts text to a natural human voice audio file.
    
    text: what we want to say
    output_path: where to save the audio file
    """
    
    response = client.audio.speech.create(
        model="tts-1",          # OpenAI's TTS model
        voice="nova",           # nova sounds natural and clear
        input=text,
        speed=0.95              # slightly slower than default, more natural on phone
    )
    
    # Save the audio file
    response.stream_to_file(output_path)
    
    return output_path


def transcribe_audio(audio_path):
    """
    Converts audio file to text using OpenAI Whisper.
    
    audio_path: path to the audio file to transcribe
    returns: the text of what was said
    """
    
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"       # we know it's English
        )
    
    return transcript.text