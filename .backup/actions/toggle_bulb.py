# actions/toggle_bulb.py

import asyncio
from pywizlight import discovery


def run(args):
    """
    Toggle your Wiz bulb ON or OFF.
    Expects args = {
        "turn_on": True/False
    }
    """

    # 1. Validate args
    if "turn_on" not in args:
        raise ValueError("Missing required argument: turn_on")
    turn_on = args["turn_on"]

    async def control_bulb():
        # Discover bulbs on your network
        bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
        if not bulbs:
            return "No bulbs found."

        light = bulbs[0]  # pick the first bulb
        if turn_on:
            await light.turn_on()
            return "Light turned ON"
        else:
            await light.turn_off()
            return "Light turned OFF"

    # 2. Run the async part and return result
    return asyncio.run(control_bulb())
