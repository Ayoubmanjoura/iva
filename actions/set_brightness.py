import asyncio
from pywizlight import PilotBuilder
from actions._bulb import get_bulb


def run(args):
    brightness = int(args["brightness"])  # already range-validated by manifest

    async def _run():
        light = await get_bulb()
        await light.turn_on(PilotBuilder(brightness=brightness))
        return f"Brightness set to {brightness}."

    return asyncio.run(_run())