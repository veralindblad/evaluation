# LATENCY

# vi behöver en funktion/metod som kör hela systemet
# samt ett tydligt "return" så att vi vet när det är klart

import time

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
    
    def get_all_records(self):
        return self.records
    

tracker = LatencyTracker()

start = tracker.start_task()    # Start (input skickas in)
answers = # systemet körs
elapsed = tracker.end_task(start, "namn") # Stopp (output klar)
