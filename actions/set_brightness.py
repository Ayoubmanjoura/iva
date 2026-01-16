# actions/set_brightness.py

import asyncio
from pywizlight import PilotBuilder, discovery


def run(args):
    """
    Sets the brightness of the first discovered Wiz bulb.
    Expects args = { "brightness": "int (0-255)" }
    """

    # 1. Validate args
    brightness = args.get("brightness")
    if brightness is None:
        raise ValueError("Missing required argument: brightness")

    try:
        brightness = int(brightness)
    except ValueError:
        raise ValueError("Brightness must be an integer")

    # 2. Optional security checks
    if brightness < 0 or brightness > 255:
        raise ValueError("Brightness must be between 0 and 255")

    # 3. Do the thing
    async def set_brightness():
        bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
        if not bulbs:
            return "No bulbs found."

        light = bulbs[0]
        await light.turn_on(PilotBuilder(brightness=brightness))
        return f"Brightness set to {brightness}"

    # 4. Run the async function and return result
    return asyncio.run(set_brightness())
