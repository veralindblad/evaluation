import time
import requests
import statistics
import math
import matplotlib.pyplot as plt



class LatencyTracker:
    # Klassen används för att hålla koll på mätningar.
    # Den kan starta tidtagning, stoppa och spara resultatet.

    def __init__(self):
        self.records = []

    def start_task(self):
        return time.perf_counter()

    def end_task(self, start_time, task_name=None):
        elapsed = time.perf_counter() - start_time
        self.records.append({'task': task_name, 'latency': elapsed})
        return elapsed

    def get_all_records(self):
        return self.records


def create_session(api_key):
    # Skapar en ny session i API:et

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
    # Skickar fråga direkt till en specifik agent

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
    print("Text:", response.text)

    response.raise_for_status()
    return response.json()


api_key = "sk_dev_6c1f33e313ea83eef3ce795c0e68c4de9e8d3e1f933367c1da05107a6ac4b87a"
#get_agents(api_key)
session_id = create_session(api_key)
agent_id = "48139f48-9ebe-4a1c-ba18-1cec7cdf4ad2"   # byt till rätt agent-id
runs = 1

latencies = []
tracker = LatencyTracker()

question = (
   "Blodet måste kunna transportera både syre och koldioxid. I vilken form finns den största delen av den koldioxid som förs runt i blodet?"
)

for i in range(runs):
    start = tracker.start_task()

    try:
        output = run_single_agent(
            message=question,
            session_id=session_id,
            agent_id=agent_id,
            api_key=api_key
        )

        elapsed = tracker.end_task(start, "gp_agent")
        latencies.append(elapsed)

        print(f"Körning {i+1}: {elapsed:.3f} sekunder")
        print("Svar:", output)

    except Exception as e:
        print("Något gick fel:", e)


