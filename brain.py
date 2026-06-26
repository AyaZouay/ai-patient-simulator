# brain.py
# This is the "thinking" part of the bot
# It reads what the agent just said and decides what the patient should say next

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load our API keys from .env file
load_dotenv()

# Connect to OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_next_response(conversation_history, scenario, agent_said):
    """
    Takes the full conversation so far and what the agent just said,
    returns what the patient should say next.
    
    conversation_history: list of previous exchanges
    scenario: the current test scenario (from scenarios.py)
    agent_said: the latest thing the agent said (transcribed text)
    """
    
    # Build the system prompt - this tells GPT who it is and what to do
    system_prompt = f"""
    You are simulating a patient calling a medical practice's AI phone agent.
    
    Your persona: {scenario['persona']}
    Your goal for this call: {scenario['goal']}
    
    Rules:
    - Keep responses short and natural, like a real phone call (1-2 sentences max)
    - If the agent asks you to create a profile, accept and give the necessary informations, use made up information.
    - Stay in character as the patient
    - React naturally to what the agent says
    - If your goal is achieved, wrap up the conversation politely
    - If the agent says something wrong or confusing, react like a real patient would
    - Do not break character
    - Do not repeat yourself unnecessarily
    - If the conversation has gone on long enough (goal achieved or clearly stuck), 
      end with "Thank you, goodbye." so we know to hang up
    """
    
    # Add the latest agent response to conversation history
    conversation_history.append({
        "role": "user",  # from patient's perspective, agent is "user"
        "content": f"The agent just said: {agent_said}"
    })
    
    # Ask GPT what the patient should say next
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history
        ],
        max_tokens=150,  # keep responses short
        temperature=0.7  # some randomness to sound natural
    )
    
    # Extract the text response
    patient_response = response.choices[0].message.content.strip()
    
    # Add patient response to history for next turn
    conversation_history.append({
        "role": "assistant",
        "content": patient_response
    })
    
    return patient_response, conversation_history


def should_end_call(patient_response):
    """
    Checks if the patient said goodbye, meaning we should hang up.
    """
    end_phrases = ["goodbye", "thank you, goodbye", "bye", "that's all i needed"]
    return any(phrase in patient_response.lower() for phrase in end_phrases)