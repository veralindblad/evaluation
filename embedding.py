from openai import OpenAI
import numpy as np
import os

client = OpenAI(api_key=os.getenv("openai_api_key"))

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return np.array(response.data[0].embedding)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def grade_with_embeddings(reference, student_answer):
    ref_emb = get_embedding(reference)
    ans_emb = get_embedding(student_answer)

    similarity = cosine_similarity(ref_emb, ans_emb)

    return {
        "similarity": float(similarity)
    }

    
def create_session(api_key):
    url = "http://localhost:8000/api/v1/sessions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, timeout=30)
    print("Create session status:", response.status_code)
    print("Create session text:", response.text)

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

    print("Status:", response.status_code)
    #print("Text:", response.text)

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



def initialize_csv_if_needed(file):
    if not os.path.exists(file):
        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "run",
                "question_id",
                "similarity"
            ])


def append_result_to_csv(file, row):
    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def get_last_completed_position(csv_filename, total_questions):
    if not os.path.exists(csv_filename) or os.path.getsize(csv_filename) == 0:
        return 1, 1

    with open(csv_filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        if not rows:
            return 1, 1

        last_row = rows[-1]
        last_run = int(last_row["run"])
        last_question_id = int(last_row["question_id"])

    if last_question_id == total_questions:
        return last_run + 1, 1
    else:
        return last_run, last_question_id + 1



# -----------------------
# MAIN EXPERIMENT
# -----------------------
def run_accuracy_experiment(api_key, agent_id, questions_file, results_file, total_runs):
    questions = load_questions_from_file(questions_file)
    initialize_csv_if_needed(results_file)

    total_questions = len(questions)

    start_run, start_question_id = get_last_completed_position(results_file, total_questions)
    print(f"Fortsätter från run {start_run}, question_id {start_question_id}")

    session_id = create_session(api_key)

    questions_by_id = {q["question_id"]: q for q in questions}

    for run_number in range(start_run, total_runs + 1):
        print(f"\n========== RUN {run_number}/{total_runs} ==========")

        if run_number == start_run:
            current_question_ids = [
                q["question_id"] for q in questions if q["question_id"] >= start_question_id
            ]
        else:
            current_question_ids = [q["question_id"] for q in questions]

        for question_id in current_question_ids:
            question_data = questions_by_id[question_id]

            question = question_data["question"]
            reference = question_data["reference"]

            print(f"\nKör run {run_number}, fråga {question_id}")

            try:
              
                response = run_single_agent(
                    message=question,
                    session_id=session_id,
                    agent_id=agent_id,
                    api_key=api_key
                )

                student_answer = response

                grade = grade_with_embeddings(reference, student_answer)

                similarity = grade["similarity"]

                append_result_to_csv(results_file, [
                    run_number,
                    question_id,
                    similarity
                ])

                print(f"✓ Sparat: similarity={similarity:.4f}")

            except Exception as e:
                print(f"Fel vid run {run_number}, fråga {question_id}: {e}")
                print("Starta om scriptet för att fortsätta.")
                return

            time.sleep(0.5)

    print("\nAlla körningar klara.")


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    api_key = "sk_dev_2cd3cb37bbc62ac0c9bc65b06dbf50d95b4d7f506bd0a881904e66c6455646ce"
    agent_id = "15128ed2-0207-4f5f-b20f-a29ca3ebb536"
    questions_file = "/Users/noraboghammar/CLARA_API/evaluation/test2q.txt"
    results_file = "accuracy_embedding_results.csv"
    total_runs = 3

    run_accuracy_experiment(
        api_key=api_key,
        agent_id=agent_id,
        questions_file=questions_file,
        results_file=results_file,
        total_runs=total_runs
    )