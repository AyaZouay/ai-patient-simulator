# Architecture

## Overview

ai-patient-simulator is a voice testing agent that makes outbound phone calls,
simulates patient conversations using AI, and records the results. The goal is
to stress-test a live healthcare voice agent across a range of realistic and
edge-case scenarios.

---

## How the system is structured

The system has five components that work together during each call:

**caller.py** is the entry point and coordinator. It starts the call via Twilio,
runs the Flask server that handles incoming webhooks, and manages the state of
the conversation — current scenario, turn count, conversation history, and
whether the call has ended.

**brain.py** is the decision layer. After each agent response is transcribed,
brain.py sends the full conversation history and the current patient persona to
GPT-4o, which returns the next patient response. It also detects when the
patient should hang up based on the content of the response.

**voice.py** handles all audio conversion. It uses OpenAI TTS to convert the
patient's text responses to speech, and OpenAI Whisper to transcribe the agent's
audio responses back to text.

**scenarios.py** defines the 11 test cases. Each scenario has a patient persona,
a goal, and an opening line. The persona is passed to GPT-4o as part of the
system prompt so the bot stays in character throughout the call.

**reporter.py** handles output. It saves a structured transcript after each call
and uses pydub to merge the individual audio turn files into one complete MP3.

---

## Call flow
python caller.py 1

│

▼

Twilio dials +1-805-439-8008

│

▼

Call connects → Flask receives POST /call/start

│

▼

TTS converts opening line to audio → served to Twilio → agent hears it

│

▼

Agent responds → Twilio records audio → sends to POST /call/respond

│

▼

Whisper transcribes agent audio

│

▼

GPT-4o reads conversation history → generates next patient response

│

▼

TTS converts response to audio → served to Twilio → agent hears it

│

▼

Loop repeats until patient says goodbye or max turns reached

│

▼

Transcript saved + audio turns merged into complete MP3

---

## Key design decisions

These decisions were made to optimize for rapid iteration and reliable testing
rather than production-scale deployment.

**Why Flask + ngrok instead of a hosted server**

Twilio needs a public URL to send audio data to after each recording. Rather
than deploying a server, I used Flask locally with ngrok to expose it publicly.
This keeps the setup simple and free — no cloud infrastructure needed for a
testing tool.

**Why OpenAI for everything**

TTS, Whisper, and GPT-4o all come from one API with one key and one billing
account. Using a single provider reduced integration complexity and simplified
authentication, billing, and maintenance. For a prototype testing tool, I
prioritized simplicity over provider flexibility.

**Why turn-based recording instead of full call recording**

Each conversation turn is recorded and transcribed individually rather than
recording the full call as one file. This gives Whisper shorter, cleaner audio
segments to transcribe — which improves accuracy. Recording shorter segments
also made it easier to associate each transcription with the correct speaker
and conversation turn during debugging. The individual turns are then merged
into one complete MP3 at the end of each call using pydub.

**Why pydub for merging**

pydub gives simple programmatic control over audio ordering and spacing. The
merge happens locally after the call ends so there's no dependency on Twilio's
recording storage or timing.

**Why max turns instead of timeout**

Conversations end either when the patient says goodbye or when a max turn limit
is reached. A turn limit is more predictable than a timeout — it prevents the
bot from running indefinitely if the agent gets stuck in a loop, which I
encountered during early testing.

---

## What I would improve

- **Voice gender matching** — all patient personas currently use the same TTS
voice regardless of gender. Matching voice to persona would make conversations
feel more realistic.

- **Agent dead-end detection** — when the agent says "Goodbye" mid-call, the
bot sometimes continues trying to respond. Adding detection for agent-initiated
endings would make the flow cleaner.

- **Parallel scenario runs** — right now calls run one at a time. With proper
state isolation, multiple scenarios could run in parallel to speed up testing.

- **Structured output from GPT-4o** — currently GPT-4o returns free-form text.
Asking it to return structured JSON with fields like `response`, `end_call`,
and `confidence` would make the decision logic more reliable.

- **Conversation memory** — right now the bot relies entirely on conversation
history passed to GPT-4o. Maintaining structured state — appointment date,
provider name, medication name — would improve consistency during longer or
more complex interactions and reduce the chance of the bot contradicting itself
across turns.