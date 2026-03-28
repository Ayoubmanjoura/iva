import asyncio
from pywizlight import PilotBuilder
from actions._bulb import get_bulb


def run(args):
    temp = int(args["temperature"])

    async def _run():
        light = await get_bulb()
        await light.turn_on(PilotBuilder(colortemp=temp))
        return f"Color temperature set to {temp}K."

    return asyncio.run(_run())