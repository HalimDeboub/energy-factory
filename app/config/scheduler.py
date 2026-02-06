import schedule
import time
from datetime import datetime
from tools.data_fetcher import RTEDataFetcher
import shutil

def job():
    fetcher = RTEDataFetcher()
    fetcher.fetch_latest()

# Schedule every 16 minutes (after API update)
schedule.every(16).minutes.do(job)

# Initial fetch on startup
print(f"⚡ Démarrage du scheduler à {datetime.now():%H:%M:%S}")
job()



def check_disk_space():
    """Prevent SQLite corruption from full disk"""
    free_gb = shutil.disk_usage(".").free / (1024**3)
    if free_gb < 1.0:  # Less than 1GB free
        raise RuntimeError(
            f"❌ CRITICAL: Only {free_gb:.1f}GB disk space left! "
            "SQLite will corrupt on next write. Free up space immediately."
        )

# Keep alive
while True:
    check_disk_space()
    schedule.run_pending()
    time.sleep(30)  # Check every 30s