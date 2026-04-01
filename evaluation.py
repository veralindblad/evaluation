# LATENCY

# Vi mäter hur lång tid systemet tar från input till output (end-to-end).
# Koden kör flera gånger (loop) och räknar ut medelvärde och spridning för x antal körningar.

import time
import requests
import statistics
import math
import matplotlib.pyplot as plt



class LatencyTracker:
    # Klassen används för att hålla koll på mätningar.
    # Den kan starta tidtagning, stoppa och spara resultatet.

    def __init__(self):
        self.records = []   # Lista där vi sparar latency

    def start_task(self):   # Startar tidtagning
        return time.perf_counter()
    
    def end_task(self, start_time, task_name=None): # Stoppar tidtagning och räknar elapsed time
        elapsed = time.perf_counter() - start_time
        self.records.append({'task': task_name, 'latency': elapsed})
        return elapsed
    
    def get_all_records(self):  # Returnerar listan
        return self.records
    

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

api_key="sk_dev_6c1f33e313ea83eef3ce795c0e68c4de9e8d3e1f933367c1da05107a6ac4b87a"
session_id = create_session(api_key)
runs = 3    # Antal körningar

latencies = []  # Sparar alla tider i sekunder

tracker = LatencyTracker()

for i in range(runs):
    # Loopen körs lika många gånger som runs

    start = tracker.start_task()    # Start för tidtagning (innan frågan skickas till systemet)

    try:    
        output = run_multiagent_system(     # Själva systemet körs (skickar fråga och får output)
        "Vad är symptomen för feber?",
        session_id=session_id,
        api_key=api_key
        )
        elapsed = tracker.end_task(start, "namn") # Stopp för tidtagning (elapsed tid räknas ut)

        latencies.append(elapsed)
        print(f"Tid: {elapsed:.3f} sekunder")

    except Exception as e:
        print("Något gick fel:", e)


# Statistik
        
mean_latency = statistics.mean(latencies)   # Medelvärde för tiderna
std_latency = statistics.stdev(latencies)   # Standardavvikelse

margin_of_error = 1.96 * (std_latency / math.sqrt(runs))    # Felmarginal för 95% konfidensintervall

lower_bound = mean_latency - margin_of_error # Nedre och 
upper_bound = mean_latency + margin_of_error # övre gräns för konfidensintervall

print(f"Medelvärde: {mean_latency:.3f}")
print(f"95% konfidensintervall: [{lower_bound:.3f}, {upper_bound:.3f}]")


# Plottar
# Plot 1: latency per körning
plt.figure()

runs_index = range(1, len(latencies)+1)

plt.plot(runs_index, latencies, marker='o')

plt.xlabel("Körning")
plt.ylabel("Tid (sekunder)")
plt.title("Latency per körning")
plt.xticks(runs_index)
plt.grid()
plt.show()


# Plot 2: histogram
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

plt.figure()

# Histogram (välj EN – här kör vi auto)
plt.hist(latencies, bins='auto')

# Vertikala linjer
plt.axvline(mean_latency, linestyle='--', label=f"Medel: {mean_latency:.2f}s")
plt.axvline(lower_bound, linestyle=':', label="95% CI")
plt.axvline(upper_bound, linestyle=':')

# Labels
plt.xlabel("Tid (sekunder)")
plt.ylabel("Antal körningar")
plt.title("Fördelning av latency")

# Heltal på y-axeln
plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Grid + legend
plt.grid()
plt.legend()

plt.show()