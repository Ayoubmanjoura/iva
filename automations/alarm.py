import schedule
import time
import asyncio
import sys
from pywizlight import PilotBuilder, discovery

# =========================
# Windows asyncio fix
# =========================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BROADCAST = "192.168.1.255"
SCENE_NUMBER = 31  # Pulse

bulbs = []
loop = None


# =========================
# Async helpers
# =========================
async def discover_bulbs():
    return await discovery.discover_lights(broadcast_space=BROADCAST)


async def activate_scene_all(scene_number):
    for bulb in bulbs:
        await bulb.turn_on(PilotBuilder(scene=scene_number))


# =========================
# Automation functions
# =========================
def morning_automation():
    print("[AUTO] 07:30 automation fired")
    loop.call_soon_threadsafe(asyncio.create_task, activate_scene_all(SCENE_NUMBER))


def evening_automation():
    print("[AUTO] 19:30 automation fired")
    loop.call_soon_threadsafe(asyncio.create_task, activate_scene_all(SCENE_NUMBER))


# =========================
# Scheduler thread entry
# =========================
def start_scheduler():
    global bulbs, loop

    print("[AUTO] Initializing asyncio loop...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("[AUTO] Discovering bulbs...")
    bulbs = loop.run_until_complete(discover_bulbs())

    if not bulbs:
        print("[AUTO] ❌ No bulbs found. Aborting scheduler.")
        return

    print(f"[AUTO] ✅ Found {len(bulbs)} bulb(s). Ready.")

    schedule.every().day.at("09:00").do(morning_automation)
    schedule.every().day.at("19:30").do(evening_automation)

    try:
        while True:
            schedule.run_pending()
            loop.run_until_complete(asyncio.sleep(1))
    finally:
        loop.close()
