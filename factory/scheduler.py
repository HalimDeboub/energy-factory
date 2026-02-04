import schedule
import time
from datetime import datetime
from data_fetcher import RTEDataFetcher

def job():
    fetcher = RTEDataFetcher()
    fetcher.fetch_latest()

# Schedule every 16 minutes (after API update)
schedule.every(16).minutes.do(job)

# Initial fetch on startup
print(f"⚡ Démarrage du scheduler à {datetime.now():%H:%M:%S}")
job()

# Keep alive
while True:
    schedule.run_pending()
    time.sleep(30)  # Check every 30s