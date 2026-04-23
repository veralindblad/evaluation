from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import requests 

load_dotenv()

client = OpenAI(api_key=os.getenv("openai_api_key"))

def grade_answer(question, reference, student_answer):
    prompt = f"""
You are a strict but fair grader.

Grade the student's answer based on:
- correctness (0-2)
- completeness (0-2)
- clarity (0-1)

Return ONLY valid JSON in this format:
{{
  "correctness": int,
  "completeness": int,
  "clarity": int,
  "total": int,
  "feedback": "text"
}}

Question: {question}
Reference answer: {reference}
Student answer: {student_answer}
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        temperature=0,
        messages=[
            {"role": "system", "content": "You are a strict grader."},
            {"role": "user", "content": prompt}
        ]
    )

    text = response.choices[0].message.content

    try:
        return json.loads(text)
    except:
        return {"error": text}

def create_session(api_key):
    # Metoden skapar en ny session i API:et
    # Session krävs för att kunna prata med chat-systemet

    url = "http://localhost:8000/api/v1/sessions"   # Endpoint där vi skapar sessionen

    headers = {
        "Authorization": f"Bearer {api_key}",   # Gör att vi får behörighet till API:et
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, timeout=30)  # Skapar sessionen
    print("Create session status:", response.status_code)
    print("Create session text:", response.text)

    response.raise_for_status()
    return response.json()["session_id"]    # Hämtar sessions-id    

def run_multiagent_system(message, session_id, api_key):
    # Funktionen skickar ett meddelande till systemet i en viss session och returnerar svaret från systemet

    url = f"http://localhost:8000/api/v1/sessions/{session_id}/chat"    # URL:en till chat-endpointen i just den sessionen

    payload = {
        "message": message,
        "stream": False,    # Vi får hela svaret direkt (ej bit för bit)
        "artifact_ids": []  # Skickar ej artifacts
    }

    headers = {
        "Authorization": f"Bearer {api_key}",   # API-nyckel för behörighet till innehållet
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=180)   # Här skickas frågan, vi väntar på svar i max 180s

    print("Status:", response.status_code)
    print("Text:", response.text)

    response.raise_for_status()
    return response.json()  # Returnerar svar
    
api_key = os.getenv("clara_api")
session_id = create_session(api_key)
student_answer = run_multiagent_system(
        "En 25-årig man har en solig eftermiddag i flera timmar åkt skidor i fjällen utan solglasögon. Senare på kvällen började han uppleva smärta och skavkänsla i ögonen tillsammans med ljuskänslighet och tårflöde. Vilken är den mest sannolika diagnosen?",
        session_id=session_id,
        api_key=api_key)


result = grade_answer(
    "En 25-årig man har en solig eftermiddag i flera timmar åkt skidor i fjällen utan solglasögon. Senare på kvällen började han uppleva smärta och skavkänsla i ögonen tillsammans med ljuskänslighet och tårflöde. Vilken är den mest sannolika diagnosen?",
    "fotoelektrisk keratit",
    student_answer
    )

print(result)