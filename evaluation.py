# LATENCY

# vi behöver en funktion/metod som kör hela systemet
# samt ett tydligt "return" så att vi vet när det är klart

import time
import requests

class LatencyTracker:
    def __init__(self):
        self.records = []

    def start_task(self):
        """Returnerar en starttid som sedan används för stopp."""
        return time.time()
    
    def end_task(self, start_time, task_name=None):
        """Beräknar och sparar latency."""
        elapsed = time.time() - start_time
        self.records.append({'task': task_name, 'latency': elapsed})
        return elapsed
    
    def get_all_records(self):
        return self.records
    
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


def run_multiagent_system(message, session_id, api_key):
    url = f"http://localhost:8000/api/v1/sessions/{session_id}/chat"

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

api_key="sk_dev_6c1f33e313ea83eef3ce795c0e68c4de9e8d3e1f933367c1da05107a6ac4b87a"
session_id = create_session(api_key)
runs = 5

latencies = []

tracker = LatencyTracker()

for i in range(runs):

    start = tracker.start_task()    # Start (input skickas in)

    try:
        output = run_multiagent_system(
        "Vilka är symptomen för diabetes typ 2?",
        session_id=session_id,
        api_key=api_key
        )
        elapsed = tracker.end_task(start, "namn") # Stopp (output klar)

        latencies.append(elapsed)
        print(f"Tid: {elapsed:.3f} sekunder")
    except Exception as e:
        print("Något gick fel:", e)

