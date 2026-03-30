"""Player collection management."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

COLLECTIONS_PATH = Path(__file__).parent.parent / "data" / "collections.json"


def load_collections() -> dict[str, dict[str, dict[str, int]]]:
    """Load all player collections from JSON file.

    Returns:
        Dict mapping username -> faction -> unit_name -> quantity (in minimum unit sizes)
    """
    if not COLLECTIONS_PATH.exists():
        log.warning(f"Collections file not found: {COLLECTIONS_PATH}")
        return {}

    try:
        with open(COLLECTIONS_PATH) as f:
            data = json.load(f)
        return data.get("collections", {})
    except Exception as e:
        log.error(f"Failed to load collections: {e}")
        return {}


def get_player_factions(username: str) -> list[str]:
    """Get list of factions a player has collections for.

    Args:
        username: The player's username (case-insensitive)

    Returns:
        List of faction names the player owns, or empty list if not found
    """
    collections = load_collections()

    username_lower = username.lower()
    for stored_user, factions in collections.items():
        if stored_user.lower() == username_lower:
            return list(factions.keys())

    return []


def get_player_collection(username: str, faction: str) -> dict[str, int] | None:
    """Get a player's collection for a specific faction.

    Args:
        username: The player's username (case-insensitive)
        faction: The faction name (case-insensitive)

    Returns:
        Dict mapping unit_name -> quantity, or None if not found
    """
    collections = load_collections()

    # Case-insensitive lookup for username
    username_lower = username.lower()
    for stored_user, factions in collections.items():
        if stored_user.lower() == username_lower:
            # Case-insensitive lookup for faction
            faction_lower = faction.lower()
            for stored_faction, units in factions.items():
                if stored_faction.lower() == faction_lower:
                    return units

    return None


def get_min_unit_size(unit) -> int:
    """Get the minimum unit size from a unit's options."""
    if not unit.options:
        return 1
    return min(opt.models for opt in unit.options)
