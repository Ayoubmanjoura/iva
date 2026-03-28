"""
Shared bulb helper for all Wiz actions.
Discovers the bulb IP once per session and caches it.
Each action gets a fresh wizlight instance (safe across asyncio.run() calls),
but skips the expensive UDP broadcast after the first call.
"""
import asyncio
from pywizlight import wizlight, discovery

BROADCAST = "192.168.1.255"
DISCOVERY_TIMEOUT = 5  # seconds

_cached_ip: str | None = None


async def get_bulb() -> wizlight:
    """
    Async — await this inside your coroutine, don't call with asyncio.run().
    Discovers the bulb IP once and caches it for the session.
    Raises RuntimeError if no bulb is found.
    """
    global _cached_ip
    if _cached_ip is None:
        bulbs = await discovery.discover_lights(
            broadcast_space=BROADCAST, wait_time=DISCOVERY_TIMEOUT
        )
        _cached_ip = bulbs[0].ip if bulbs else None
    if _cached_ip is None:
        raise RuntimeError("No Wiz bulbs found on the network.")
    return wizlight(_cached_ip)


def clear_cache() -> None:
    """Force re-discovery on the next get_bulb() call."""
    global _cached_ip
    _cached_ip = None