# actions/temperature.py

import asyncio
from pywizlight import PilotBuilder, discovery


def run(args):
    """
    Sets the color temperature of the first discovered Wiz bulb.
    Expects args = { "temperature": "int (2500-6500)" }
    """

    # 1. Validate args
    temp = args.get("temperature")
    if temp is None:
        raise ValueError("Missing required argument: temperature")

    try:
        temp = int(temp)
    except ValueError:
        raise ValueError("Temperature must be an integer")

    # 2. Optional security checks
    if temp < 2500 or temp > 6500:
        raise ValueError("Temperature must be between 2500K (warm) and 6500K (cold)")

    # 3. Do the thing
    async def set_temperature():
        bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
        if not bulbs:
            return "No bulbs found."

        light = bulbs[0]
        await light.turn_on(PilotBuilder(colortemp=temp))
        return f"Bulb set to {temp}K"

    # 4. Run the async function and return result
    return asyncio.run(set_temperature())
