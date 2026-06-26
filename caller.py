# caller.py
# This is the main file - run this to start a call
# It coordinates everything: Twilio makes the call, voice.py handles audio,
# brain.py decides what to say, reporter.py saves everything

import os
import time
import threading
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
from scenarios import SCENARIOS
from brain import get_next_response, should_end_call
from voice import text_to_speech, transcribe_audio
from reporter import save_transcript, merge_call_recordings

# Load API keys from .env file
load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL")

# ─── SETUP ────────────────────────────────────────────────────────────────────

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

# Global call state
current_scenario = None
conversation_history = []
conversation_log = []
call_turn = 0
call_ended = False  # prevents double trigger


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def download_recording(recording_url, output_path):
    """
    Downloads the agent's audio recording from Twilio.
    """
    import requests
    from requests.auth import HTTPBasicAuth

    time.sleep(2)  # wait for recording to be ready

    response = requests.get(
        recording_url + ".mp3",
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    )

    with open(output_path, "wb") as f:
        f.write(response.content)


def end_call_cleanup():
    """
    Saves transcript and merges recordings.
    Called once when the call ends, regardless of how it ended.
    """
    global call_ended, conversation_log

    if call_ended:
        return  # already cleaned up, don't run twice

    call_ended = True

    save_transcript(
        current_scenario["id"],
        current_scenario["name"],
        conversation_log
    )
    time.sleep(3)  # wait for last audio file to finish serving
    merge_call_recordings(current_scenario["id"])
    conversation_log = []


# ─── FLASK ROUTES ─────────────────────────────────────────────────────────────

@app.route("/call/start", methods=["POST"])
def call_start():
    """
    Twilio calls this URL the moment the call connects.
    We play the patient's opening line.
    """
    global call_turn, conversation_log, call_ended

    call_turn = 0
    call_ended = False  # reset for new call

    opening_line = current_scenario["opening"]

    # Convert opening line to audio
    audio_path = "recordings/turn_0_patient.mp3"
    text_to_speech(opening_line, audio_path)

    conversation_log.append({
        "speaker": "PATIENT",
        "text": opening_line
    })

    print(f"\nPATIENT: {opening_line}")

    response = VoiceResponse()
    response.play(f"{BASE_URL}/audio/turn_0_patient.mp3")
    response.record(
        action=f"{BASE_URL}/call/respond",
        max_length=30,
        finish_on_key="",
        play_beep=False
    )

    return Response(str(response), mimetype="text/xml")


@app.route("/call/respond", methods=["POST"])
def call_respond():
    """
    Twilio calls this URL after the agent has spoken.
    We transcribe, think, and respond.
    """
    global call_turn, conversation_history, conversation_log

    # Prevent double processing
    if call_ended:
        response = VoiceResponse()
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    call_turn += 1

    # Get the recording URL from Twilio
    recording_url = request.form.get("RecordingUrl")

    if not recording_url:
        end_call_cleanup()
        response = VoiceResponse()
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    # Download and save agent audio
    agent_audio_path = f"recordings/turn_{call_turn}_agent.mp3"
    download_recording(recording_url, agent_audio_path)

    # Transcribe what the agent said
    agent_said = transcribe_audio(agent_audio_path)
    print(f"\nAGENT: {agent_said}")

    conversation_log.append({
        "speaker": "AGENT",
        "text": agent_said
    })

    # Check if we've hit max turns
    if call_turn >= 12:
        print("\nMax turns reached, ending call.")
        end_call_cleanup()
        response = VoiceResponse()
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    # Ask GPT what patient should say next
    patient_response, conversation_history = get_next_response(
        conversation_history,
        current_scenario,
        agent_said
    )

    print(f"\nPATIENT: {patient_response}")

    conversation_log.append({
        "speaker": "PATIENT",
        "text": patient_response
    })

    # Convert patient response to audio
    patient_audio_path = f"recordings/turn_{call_turn}_patient.mp3"
    text_to_speech(patient_response, patient_audio_path)

    # Check if patient said goodbye
    if should_end_call(patient_response):
        print("\nPatient said goodbye, ending call.")
        end_call_cleanup()
        response = VoiceResponse()
        response.play(f"{BASE_URL}/audio/turn_{call_turn}_patient.mp3")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    # Continue conversation
    response = VoiceResponse()
    response.play(f"{BASE_URL}/audio/turn_{call_turn}_patient.mp3")
    response.record(
        action=f"{BASE_URL}/call/respond",
        max_length=30,
        finish_on_key="",
        play_beep=False
    )

    return Response(str(response), mimetype="text/xml")


@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """
    Serves audio files to Twilio.
    """
    filepath = os.path.join("recordings", filename)
    with open(filepath, "rb") as f:
        audio_data = f.read()
    return Response(audio_data, mimetype="audio/mpeg")


# ─── MAKE CALL ────────────────────────────────────────────────────────────────

def make_call(scenario_index):
    """
    Starts a call for the given scenario.
    """
    global current_scenario, conversation_history, conversation_log, call_ended

    current_scenario = SCENARIOS[scenario_index]
    conversation_history = []
    conversation_log = []
    call_ended = False

    print(f"\n{'='*50}")
    print(f"Starting call for scenario {current_scenario['id']}: {current_scenario['name']}")
    print(f"{'='*50}")

    call = twilio_client.calls.create(
        to=TARGET_PHONE_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url=f"{BASE_URL}/call/start",
        method="POST",
        record=True,
        recording_channels="dual"
    )

    print(f"Call started! SID: {call.sid}")
    return call.sid


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python caller.py <scenario_number>")
        print("Example: python caller.py 1")
        print(f"Available scenarios: 1-{len(SCENARIOS)}")
        sys.exit(1)

    scenario_num = int(sys.argv[1]) - 1

    if scenario_num < 0 or scenario_num >= len(SCENARIOS):
        print(f"Invalid scenario. Please choose 1-{len(SCENARIOS)}")
        sys.exit(1)

    # Start call in separate thread so Flask can run simultaneously
    call_thread = threading.Thread(
        target=make_call,
        args=(scenario_num,)
    )
    call_thread.start()

    print("\nStarting Flask server...")
    print("Make sure ngrok is running on port 5000!")
    app.run(port=5000, debug=False)