import asyncio
from actions._bulb import get_bulb


def run(args):
    turn_on = args["turn_on"]  # already validated by main.py

    async def _run():
        light = await get_bulb()
        if turn_on:
            await light.turn_on()
            return "Light turned ON."
        else:
            await light.turn_off()
            return "Light turned OFF."

    return asyncio.run(_run())