from openai import OpenAI
from dotenv import load_dotenv
import os
import re 
import requests
import time 


def create_session(api_key):
    url = "http://localhost:8000/api/v1/sessions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, timeout=30)

    response.raise_for_status()
    return response.json()["session_id"]


def run_single_agent(message, session_id, agent_id, api_key):
    url = f"http://localhost:8000/api/v1/sessions/{session_id}/agents/{agent_id}/chat"

    payload = {
        "message": message,
        "stream": False,
        "artifact_ids": []
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=180)

    response.raise_for_status()

    return response.json()


def load_questions_from_file(filename):
    questions = []

    with open(filename, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split("|", 2)
            if len(parts) != 3:
                print(f"Rad {line_number} hoppades över.")
                continue

            qid, question, reference = parts

            try:
                qid = int(qid.strip())
            except:
                continue

            questions.append({
                "question_id": qid,
                "question": question.strip(),
                "reference": reference.strip()
            })

    questions.sort(key=lambda x: x["question_id"])
    return questions


def run_questions_to_txt(api_key, agent_id, questions_file, output_file):
    questions = load_questions_from_file(questions_file)

    session_id = create_session(api_key)
    print(f"Session skapad: {session_id}")

    with open(output_file, "w", encoding="utf-8") as f:
        for q in questions:
            qid = q["question_id"]
            question_text = q["question"]
            reference = q["reference"]

            try:
                response = run_single_agent(
                    message=question_text,
                    session_id=session_id,
                    agent_id=agent_id,
                    api_key=api_key
                )

                ai_answer = response.get("response", "")
                ai_answer = re.sub(r"\[\^web:.*?\]", "", ai_answer).strip()
                ai_answer = " ".join(ai_answer.split())

            except Exception as e:
                ai_answer = f"ERROR: {str(e)}"

            f.write(f"{qid} | {question_text} | {reference} | {ai_answer}\n")

            time.sleep(1)

    print(f"Klart! Sparat i {output_file}")



# -----------------------
# RUN
# -----------------------
    
load_dotenv()    

if __name__ == "__main__":
    api_key = os.getenv("clara_api")
    agent_id = os.getenv("agent_id")

    run_questions_to_txt(
        api_key=api_key,
        agent_id=agent_id,
        questions_file="/Users/noraboghammar/CLARA_API/evaluation/test2q.txt",
        output_file="answers_test.txt"
    )