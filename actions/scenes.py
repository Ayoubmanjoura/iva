import asyncio
from pywizlight import PilotBuilder
from actions._bulb import get_bulb

SCENES = {
    0: "Off/None", 1: "Ocean", 2: "Romance", 3: "Sunset", 4: "Party",
    5: "Fireplace", 6: "Cozy", 7: "Forest", 8: "Pastel Colors", 9: "Wake-up",
    10: "Bedtime", 11: "Warm White", 12: "Daylight", 13: "Cool White",
    14: "Night Light", 15: "Focus", 16: "Relax", 17: "True Colors",
    18: "TV Time", 19: "Plant Growth", 20: "Spring", 21: "Summer",
    22: "Fall", 23: "Deep Dive", 24: "Jungle", 25: "Mojito", 26: "Club",
    27: "Christmas", 28: "Halloween", 29: "Candlelight", 30: "Golden White",
    31: "Pulse", 32: "Steampunk", 1000: "Rhythm",
}


def run(args):
    scene_number = int(args["scene_number"])
    if scene_number not in SCENES:
        raise ValueError(f"Invalid scene number: {scene_number}. Valid: {list(SCENES.keys())}")

    async def _run():
        light = await get_bulb()
        await light.turn_on(PilotBuilder(scene=scene_number))
        return f"Scene set to {SCENES[scene_number]}."

    return asyncio.run(_run())