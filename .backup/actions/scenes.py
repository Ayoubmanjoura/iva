import asyncio
from pywizlight import PilotBuilder, discovery

SCENES = {
    0: "Off/None",
    1: "Ocean",
    2: "Romance",
    3: "Sunset",
    4: "Party",
    5: "Fireplace",
    6: "Cozy",
    7: "Forest",
    8: "Pastel Colors",
    9: "Wake-up",
    10: "Bedtime",
    11: "Warm White",
    12: "Daylight",
    13: "Cool White",
    14: "Night Light",
    15: "Focus",
    16: "Relax",
    17: "True Colors",
    18: "TV Time",
    19: "Plant Growth",
    20: "Spring",
    21: "Summer",
    22: "Fall",
    23: "Deep Dive",
    24: "Jungle",
    25: "Mojito",
    26: "Club",
    27: "Christmas",
    28: "Halloween",
    29: "Candlelight",
    30: "Golden White",
    31: "Pulse",
    32: "Steampunk",
}


def run(args):
    scene_number = args.get("scene_number")
    if scene_number is None:
        raise ValueError("Missing required argument: scene_number")

    try:
        scene_number = int(scene_number)
    except ValueError:
        raise ValueError("Scene number must be an integer")

    if scene_number not in SCENES:
        raise ValueError(f"Scene number must be one of {list(SCENES.keys())}")

    async def set_scene():
        bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
        if not bulbs:
            return "No bulbs found."

        light = bulbs[0]
        await light.turn_on(PilotBuilder(scene=scene_number))
        return f"Activated scene {scene_number}: {SCENES[scene_number]}"

    return asyncio.run(set_scene())
