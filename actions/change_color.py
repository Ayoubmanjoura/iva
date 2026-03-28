import asyncio
from pywizlight import PilotBuilder
from actions._bulb import get_bulb


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))


def run(args):
    hex_color: str = args["hex_color"]

    async def _run():
        light = await get_bulb()
        rgb = _hex_to_rgb(hex_color)
        await light.turn_on(PilotBuilder(rgb=rgb))
        return f"Color set to {hex_color.upper()}."

    return asyncio.run(_run())