# actions/change_color.py

import asyncio
from pywizlight import PilotBuilder, discovery


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def run(args):
    """
    Sets the color of the first discovered Wiz bulb using a HEX color.
    Expects args = { "hex_color": "#RRGGBB" }
    """

    # 1. Validate args
    hex_color = args.get("hex_color")
    if not hex_color:
        raise ValueError("Missing required argument: hex_color")

    # 2. Optional security checks
    forbidden_colors = ["#000000"]  # example: black might be forbidden
    if hex_color.upper() in forbidden_colors:
        raise PermissionError("This color is not allowed")

    # 3. Do the thing
    async def set_color():
        bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
        if not bulbs:
            return "No bulbs found."

        light = bulbs[0]
        rgb = hex_to_rgb(hex_color)
        await light.turn_on(PilotBuilder(rgb=rgb))
        state = await light.updateState()
        return f"RGB set to: {state.get_rgb()}"

    # 4. Run the async function and return result
    return asyncio.run(set_color())
