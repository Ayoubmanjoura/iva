import schedule
import time
import asyncio
import sys

# =========================
# Windows asyncio fix
# =========================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =========================
# Optional constants (replace or add as needed)
{constants}  # e.g., BULB_IP = "192.168.1.100"

# =========================
# Import the action module
from actions import {action_module}  # AI replaces {action_module} with the action to run

# =========================
# Async wrapper for actions
async def run_action():
    # if action is async, use await
    {async_line}  # e.g., await toggle_bulb.run({"turn_on": True})
    # if action is sync, just call
    # {action_module}.run({action_args})

# =========================
# Automation job
def automation_job():
    print(f"[AUTO] {trigger_time} automation fired")
    loop.call_soon_threadsafe(asyncio.create_task, run_action())

# =========================
# Scheduler entry
def start_scheduler():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # optional setup, e.g., bulb discovery
    {setup_lines}  # AI can leave blank if not needed

    # schedule the job
    schedule.every().day.at("{trigger_time}").do(automation_job)

    try:
        while True:
            schedule.run_pending()
            loop.run_until_complete(asyncio.sleep(1))
    finally:
        loop.close()

# =========================
# Run scheduler
if __name__ == "__main__":
    start_scheduler()
