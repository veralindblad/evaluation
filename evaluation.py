# LATENCY

# vi behöver en funktion/metod som kör hela systemet
# samt ett tydligt "return" så att vi vet när det är klart

import time
import requests
import statistics
import math
import matplotlib.pyplot as plt

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
runs = 3

latencies = []

tracker = LatencyTracker()

for i in range(runs):

    start = tracker.start_task()    # Start (input skickas in)

    try:
        output = run_multiagent_system(
        "Vad är symptomen för feber?",
        session_id=session_id,
        api_key=api_key
        )
        elapsed = tracker.end_task(start, "namn") # Stopp (output klar)

        latencies.append(elapsed)
        print(f"Tid: {elapsed:.3f} sekunder")
    except Exception as e:
        print("Något gick fel:", e)


mean_latency = statistics.mean(latencies)
std_latency = statistics.stdev(latencies)

margin_of_error = 1.96 * (std_latency / math.sqrt(runs))

lower_bound = mean_latency - margin_of_error
upper_bound = mean_latency + margin_of_error

print(f"Medelvärde: {mean_latency:.3f}")
print(f"95% konfidensintervall: [{lower_bound:.3f}, {upper_bound:.3f}]")


# Plottar

# Latency per körning
plt.plot(latencies)
plt.xlabel("Körning")
plt.ylabel("Tid (sekunder)")
plt.title("Latency per körning")

plt.show()


# Histogram
plt.hist(latencies, bins=5)

plt.xlabel("Tid (sekunder)")
plt.ylabel("Antal")
plt.title("Fördelning av latency")

plt.show()