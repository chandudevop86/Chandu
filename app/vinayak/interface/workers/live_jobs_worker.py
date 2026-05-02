import time
from app.vinayak.interface.api.services.live_analysis_jobs import process_next_live_analysis_job

while True:
    worked = process_next_live_analysis_job()
    if not worked:
        time.sleep(2)