import csv
import os
import time
import requests


class LatencyTracker:
    def __init__(self):
        self.records = []

    def start_task(self):
        return time.perf_counter()

    def end_task(self, start_time, task_name=None, difficulty=None, question_id=None):
        elapsed = time.perf_counter() - start_time
        record = {
            "task": task_name,
            "question_id": question_id,
            "difficulty": difficulty,
            "latency": elapsed
        }
        self.records.append(record)
        return elapsed


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
                print(f"Rad {line_number} hoppades över: fel format.")
                continue

            question_id_str, difficulty, question = parts

            try:
                question_id = int(question_id_str.strip())
            except ValueError:
                print(f"Rad {line_number} hoppades över: ogiltigt question_id.")
                continue

            difficulty = difficulty.strip().lower()
            question = question.strip()

            if difficulty not in ["easy", "medium", "hard"]:
                print(f"Rad {line_number} hoppades över: ogiltig svårighetsgrad.")
                continue

            questions.append({
                "question_id": question_id,
                "difficulty": difficulty,
                "question": question
            })

    questions.sort(key=lambda x: x["question_id"])
    return questions


def initialize_csv_if_needed(csv_filename):
    if not os.path.exists(csv_filename):
        with open(csv_filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["run", "question_id", "difficulty", "latency"])


def append_result_to_csv(csv_filename, run_number, question_id, difficulty, latency):
    with open(csv_filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([run_number, question_id, difficulty, f"{latency:.6f}"])
        file.flush()
        os.fsync(file.fileno())


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


def run_latency_experiment(api_key, agent_id, questions_file, results_file, total_runs):
    questions = load_questions_from_file(questions_file)

    if not questions:
        raise ValueError("Inga giltiga frågor hittades i frågefilen.")

    initialize_csv_if_needed(results_file)

    total_questions = len(questions)
    start_run, start_question_id = get_last_completed_position(results_file, total_questions)

    print(f"Fortsätter från run {start_run}, question_id {start_question_id}")

    session_id = create_session(api_key)
    tracker = LatencyTracker()

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
            difficulty = question_data["difficulty"]
            question = question_data["question"]

            print(f"\nKör run {run_number}, fråga {question_id}, svårighetsgrad {difficulty}")

            start_time = tracker.start_task()

            try:
                output = run_single_agent(
                    message=question,
                    session_id=session_id,
                    agent_id=agent_id,
                    api_key=api_key
                )

                elapsed = tracker.end_task(
                    start_time=start_time,
                    task_name=f"run_{run_number}_question_{question_id}",
                    difficulty=difficulty,
                    question_id=question_id
                )

                append_result_to_csv(
                    csv_filename=results_file,
                    run_number=run_number,
                    question_id=question_id,
                    difficulty=difficulty,
                    latency=elapsed
                )

                print(f"Sparat: run={run_number}, question_id={question_id}, latency={elapsed:.3f} s")
                print("Svar:", output)

            except Exception as e:
                print(f"Fel vid run {run_number}, fråga {question_id}: {e}")
                print("Programmet stoppas. Starta om det för att fortsätta från senaste sparade rad.")
                return

            time.sleep(0.5)

    print("\nAlla körningar är klara.")


if __name__ == "__main__":
    api_key = "sk_dev_6c1f33e313ea83eef3ce795c0e68c4de9e8d3e1f933367c1da05107a6ac4b87a"
    agent_id = "48139f48-9ebe-4a1c-ba18-1cec7cdf4ad2"
    questions_file = "/Users/veralindblad/Documents/CLARA_API/evaluation/testq.txt"
    results_file = "latency_results.csv"
    total_runs = 3

    run_latency_experiment(
        api_key=api_key,
        agent_id=agent_id,
        questions_file=questions_file,
        results_file=results_file,
        total_runs=total_runs
    )