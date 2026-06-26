# Bug Report — Pretty Good AI Voice Agent Testing

**Tester:** Aya Zouay  
**Test Date:** June 24-26, 2026  
**Test Number:** +1-805-439-8008  
**Tool:** ai-patient-simulator — automated voice testing agent  
**Total Calls Made:** 11  
**Total Bugs Found:** 12  

---

## Before I Start

I built an automated voice bot that called Pretty Good AI's test line and simulated different patient scenarios — scheduling, refills, edge cases, and frustrated callers. Going in, I expected to find a few rough edges. What I didn't expect was a consistent pattern: the agent handles the conversation well up until it actually needs to do something, and then it fails. Almost every call. That became the thread I pulled on through all 11 tests.

Some of the behaviors below may be intentional for the test environment — the transfer dead end in particular. I've noted where that's likely the case. Everything else I'd consider worth investigating before production.

---

## Summary Table

| Bug # | Title | Severity | Scenario |
|-------|-------|----------|----------|
| 1 | Placeholder provider name exposed to patient | Medium | 1 |
| 2 | Non-human identifier exposed as provider name | High | 1 |
| 3 | Agent proceeds after date of birth mismatch | High | 1 |
| 4 | Caller identity assumed from phone number alone | High | 2, 4, 9 |
| 5 | Patient name misidentified without correction | Medium | 2 |
| 6 | Agent fails silently after successful verification | Critical | 2, 4, 5, 9 |
| 7 | Transfer path routes to dead end | Critical | 2, 4, 9, 10, 11 |
| 8 | Agent accepts multiple conflicting dates of birth | High | 5 |
| 9 | Agent engages with off-topic small talk | Low | 7 |
| 10 | Agent confirms phantom appointments | High | 1, 7 |
| 11 | Agent reads back phone number unprompted | Critical | 9 |
| 12 | Agent responds with incoherent unrelated text | Critical | 11 |

---

## Bug #1 — Placeholder Provider Name Exposed to Patient

**Severity:** Medium  
**Scenario:** 1 — Simple Appointment Scheduling  
**Transcript:** transcript_01  
**Timestamp:** Turn 5

**Evidence:**
> Agent: "The earliest morning appointment I found is Tuesday, June 30th at 12:45 p.m. with Doogie Houser."

**What happened:**  
When offering available slots, the agent offered an appointment with "Doogie Houser" — which appears to be a test or placeholder name.

**Why it's a problem:**  
Test provider names are surfacing in patient-facing responses. A real patient hearing this would likely question whether they're dealing with a legitimate medical service.

**Expected behavior:**  
Only verified human-readable provider names should be presented. A validation step should filter placeholder or test data before responses reach callers.

---

## Bug #2 — Non-Human Identifier Exposed as Provider Name

**Severity:** High  
**Scenario:** 1 — Simple Appointment Scheduling  
**Transcript:** transcript_01  
**Timestamp:** Turn 6

**Evidence:**
> Agent: "The earliest morning slot I found is Wednesday, July 1st at 10:30 a.m. with ABRICOR."

**What happened:**  
The agent offered an appointment with "ABRICOR" — which appears to be an internal identifier or placeholder rather than a human-readable provider name.

**Why it's a problem:**  
If this is a raw system value being passed into the patient conversation without resolution, it suggests the provider name mapping step may be incomplete. Presenting non-human identifiers to patients is confusing and undermines trust.

**Expected behavior:**  
All provider values should be resolved to verified human names before being presented. A fallback message should exist if a name cannot be resolved.

---

## Bug #3 — Agent Proceeds After Date of Birth Mismatch

**Severity:** High  
**Scenario:** 1 — Simple Appointment Scheduling  
**Transcript:** transcript_01  
**Timestamp:** Turn 2

**Evidence:**
> Agent: "The birthday doesn't match our records, but for demo purposes, I'll accept it. How can I help you today?"

**What happened:**  
The patient gave a date of birth that didn't match the record. The agent acknowledged the mismatch and proceeded anyway.

**Why it's a problem:**  
This one stood out to me because the agent literally said out loud that the information was wrong and kept going. The "demo purposes" phrasing suggests this may be test-environment behavior — but it's worth confirming that production enforces strict verification. A mismatched DOB should stop the process, not be waved through.

**Expected behavior:**  
A mismatched date of birth should halt verification and either prompt the patient to try again or escalate to a human agent.

---

## Bug #4 — Caller Identity Assumed From Phone Number Alone

**Severity:** High  
**Scenario:** 2, 4, 9  
**Transcript:** transcript_02, transcript_04, transcript_09  
**Timestamp:** Turn 0 in all cases

**Evidence:**
> Agent: "Pivot Point Orthopedics, part of Pretty Good AI. Am I speaking with Maria?"  
> Patient: "No, this is James."

**What happened:**  
Every call from the same Twilio number was greeted with "Am I speaking with Maria?" before the caller provided any information.

**Why it's a problem:**  
I first noticed this in scenario 2 and assumed it was a fluke. But it happened again in scenarios 4 and 9 with completely different patient personas. The agent is clearly using the calling number to pre-identify the caller. In a real practice, multiple people share phones — family members, caregivers, people calling from work. Assuming identity from a number alone could result in one patient being given access to another's information. This would need review against the organization's patient privacy policies.

**Expected behavior:**  
Every call should begin with fresh identity verification regardless of whether the number is recognized.

---

## Bug #5 — Patient Name Misidentified Without Correction

**Severity:** Medium  
**Scenario:** 2 — Simple Medication Refill  
**Transcript:** transcript_02  
**Timestamp:** Turn 1

**Evidence:**
> Patient: "No, this is James."  
> Agent: "Thanks for letting me know, Jane."

**What happened:**  
The agent misheard "James" as "Jane" and addressed the patient by the wrong name for the rest of the interaction.

**Why it's a problem:**  
Calling a patient by the wrong name erodes trust and raises questions about whether the right record is being used.

**Expected behavior:**  
The agent should confirm names that sound similar before proceeding. Example: "Just to confirm, did you say James?"

---

## Bug #6 — Agent Fails Silently After Successful Verification

**Severity:** Critical  
**Scenario:** 2, 4, 5, 9  
**Transcript:** transcript_02, transcript_04, transcript_05, transcript_09  
**Timestamp:** varies

**Evidence:**
> Agent: "I can't process this refill request right now, but I can connect you to our patient support team for help."  
> Agent: "I can't schedule the appointment right now, but I can connect you to our patient support team for help."

**What happened:**  
In four separate scenarios, the agent completed full identity verification and then said it couldn't process the request — with no explanation — before attempting a transfer that led nowhere.

**Why it's a problem:**  
This is the pattern I kept coming back to across all 11 calls. The agent is good at collecting information but consistently hits a wall when it needs to act on it. Scheduling fails. Refills fail. Prior auth fails. Each time the patient goes through the full verification process and leaves with nothing. That's a worse experience than not having an AI agent at all — it adds friction without delivering value.

**Expected behavior:**  
If the agent cannot complete a task, it should explain why clearly, offer an alternative, and make sure the patient can reach someone who can actually help.

---

## Bug #7 — Transfer Path Routes to Dead End

**Severity:** Critical  
**Scenario:** 2, 4, 9, 10, 11  
**Transcript:** Multiple  
**Timestamp:** varies

**Evidence:**
> Agent: "Connecting you to a representative. Please wait."  
> System: "Hello, you've reached the Pretty Good AI test line. Goodbye."

**What happened:**  
Every single transfer across all 11 calls ended with the same recorded message and disconnection.

**Why it's a problem:**  
This may be intentional for the assessment environment — if so, it should be documented as a known limitation. But in production, a broken transfer path means patients with complex needs or urgent questions have no fallback. In healthcare that's not just a bad experience — it's a safety concern.

**Expected behavior:**  
Production transfers should connect to a real person or at minimum a proper voicemail with a clear callback commitment.

---

## Bug #8 — Agent Accepts Multiple Conflicting Dates of Birth

**Severity:** High  
**Scenario:** 5 — Wrong Date of Birth  
**Transcript:** transcript_05  
**Timestamp:** Turns 2-4

**Evidence:**
> Patient: "My birthday is January 1, 1970."  
> Patient: "Actually it's February 15, 1965."  
> Patient: "Was it February 16th, 1965?"  
> Agent: "To confirm, is your date of birth February 16, 1965?" — then proceeds.

**What happened:**  
The patient gave three different dates of birth during the same call. The agent accepted the final one without flagging the inconsistency.

**Why it's a problem:**  
I designed this scenario specifically to see if the agent would catch inconsistent verification attempts. It didn't. A caller who provides multiple conflicting dates of birth is either confused or potentially trying to guess their way through verification. Either way the agent should not proceed without escalating.

**Expected behavior:**  
After two inconsistent verification attempts, the agent should stop and escalate to a human rather than accepting whatever the caller provides last.

---

## Bug #9 — Agent Engages With Off-Topic Small Talk

**Severity:** Low  
**Scenario:** 7 — Completely Off Topic Question  
**Transcript:** transcript_07  
**Timestamp:** Turn 1

**Evidence:**
> Patient: "Did you catch the game last night? It was intense!"  
> Agent: "I didn't catch it, but it sounds like it was exciting. How can I help you with your orthopedic care today?"

**What happened:**  
When the patient asked a personal off-topic question the agent responded as though it had watched the game before redirecting.

**Why it's a problem:**  
A healthcare AI responding as if it has personal experiences creates ambiguity about whether the patient is speaking with a human or an AI. Transparency about AI identity matters in patient-facing systems.

**Expected behavior:**  
The agent should clarify its nature when personal questions arise. Example: "I'm an AI assistant so I don't watch games — but I'm happy to help you with your care today."

---

## Bug #10 — Agent Confirms Phantom Appointments

**Severity:** High  
**Scenario:** 1, 7  
**Transcript:** transcript_01, transcript_07  
**Timestamp:** varies

**Evidence:**
> Agent: "It looks like you already have a new patient consultation booked. If you want to reschedule or cancel that appointment, I can help."  
> Patient: "I wasn't aware of an existing appointment."

**What happened:**  
In two scenarios with different patient personas, the agent told the caller they already had an appointment on file when neither patient had booked one. This happened in both scenario 1 and scenario 7 — different names, same calling number.

**Why it's a problem:**  
The agent appears to be surfacing appointment records based on the calling number rather than verified patient identity. Presenting incorrect appointment information to a patient could cause them to skip booking care they actually need. It also connects back to Bug #4 — the system is over-relying on phone number as an identifier throughout the call.

**Expected behavior:**  
Appointment records should only be presented after full identity verification, not based on caller ID alone.

---

## Bug #11 — Agent Reads Back Phone Number Unprompted

**Severity:** Critical  
**Scenario:** 9 — Prior Authorization Status  
**Transcript:** transcript_09  
**Timestamp:** Turn 3

**Evidence:**
> Agent: "I have your phone number as 510-907-8123 and your date of birth as April 12, 1975. Is that correct?"

**What happened:**  
The agent read back a phone number the patient never provided. The number appeared to have been pulled from a record in the system.

**Why it's a problem:**  
This caught my attention immediately. The patient never gave a phone number — the agent just read one out. If that number belongs to a different patient whose record was incorrectly matched, this is an unauthorized disclosure of personal information. This would need careful review to ensure it aligns with the organization's data handling and privacy policies.

**Expected behavior:**  
The agent should ask patients to provide their phone number rather than reading it from records unprompted. Patient data should not be disclosed unless the patient has already verified their identity and explicitly requested that information.

---

## Bug #12 — Agent Responds With Incoherent Unrelated Text

**Severity:** Critical  
**Scenario:** 11 — Impossible Date Request  
**Transcript:** transcript_11 (first attempt)  
**Timestamp:** Turn 0

**Evidence:**
> Agent: "Part 3 of 5 will be posted on the Vua Broers тобы вернуться,"

**What happened:**  
On the first attempt at scenario 11 the agent's opening response was completely unrelated to the call — incoherent text that appeared to come from an entirely different context.

**Why it's a problem:**  
This one was unexpected. The response appears unrelated to the conversation and may indicate context contamination or an unexpected generation error — I can't say for certain what caused it. What I can say is that a patient receiving this response would have no idea what was happening. If unrelated content can appear in agent responses, the system's reliability in a patient-facing context needs investigation.

**Expected behavior:**  
Safeguards should exist to detect and prevent incoherent or off-topic generations from reaching patients.

---

## Key Systemic Finding

The thing that stood out most across all 11 calls wasn't any single bug — it was the pattern.

The agent is genuinely good at the front half of a call. It handles small talk, redirects off-topic questions reasonably well, and collects patient information in a structured way. But the moment it needs to complete something — schedule an appointment, process a refill, check a prior auth status, transfer to a human — it fails. Every time.

I initially assumed this was a test environment limitation. But it happened across too many different scenarios for me to write it off. Scheduling failed. Refills failed. Prior auth failed. Escalation failed. The agent verifies identity successfully and then hits a wall.

In production that means patients call in, go through a full verification process that can take several minutes, and leave with nothing resolved. That's not just a bad experience — it's likely to push patients back to calling the front desk directly, which is the exact problem the system is supposed to solve.

That's the finding I'd prioritize above everything else.

---

## Summary by Severity

| Severity | Count | Bugs |
|----------|-------|------|
| Critical | 4 | 6, 7, 11, 12 |
| High | 5 | 2, 3, 4, 8, 10 |
| Medium | 2 | 1, 5 |
| Low | 1 | 9 |