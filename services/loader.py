"""Faction data loading and ally injection."""

import json
import logging
from pathlib import Path

from models.models import Unit, UnitOption, Enhancement, Detachment, FactionData, derive_category
from utils.constants import IMPERIUM_FACTIONS, CHAOS_FACTIONS

log = logging.getLogger(__name__)


def load_factions() -> dict[str, FactionData]:
    """Load all faction data from JSON files and inject allies."""
    factions = {}
    factions_dir = Path(__file__).parent.parent / "factions"
    if not factions_dir.exists():
        log.error(f"Factions directory not found: {factions_dir}")
        return factions

    for path in factions_dir.glob("*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
            units = [
                Unit(
                    name=u["name"],
                    options=[UnitOption(o[0], o[1]) for o in u["options"]],
                    is_unique=u.get("is_unique", False),
                    category=derive_category(u["name"], u.get("keywords", [])),
                    url=u.get("url", ""),
                    keywords=u.get("keywords", []),
                    faction_keywords=u.get("faction_keywords", []),
                )
                for u in data.get("units", [])
            ]
            detachments = [
                Detachment(d["name"], [Enhancement(e["name"], e["points"]) for e in d.get("enhancements", [])])
                for d in data.get("detachments", [])
            ]
            faction_name = data.get("faction", path.stem)
            factions[faction_name] = FactionData(units, detachments, data.get("faction_url", ""))
            log.debug(f"Loaded faction: {faction_name} ({len(units)} units, {len(detachments)} detachments)")
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in {path.name}: {e}")
        except KeyError as e:
            log.error(f"Missing required field in {path.name}: {e}")
        except Exception as e:
            log.error(f"Error loading {path.name}: {e}")

    _inject_allies(factions)

    # Build indexes for fast autocomplete after all injections
    for faction_data in factions.values():
        faction_data._build_indexes()

    return factions


def _inject_allies(factions: dict[str, FactionData]) -> None:
    """Inject ally units into factions."""
    # Inject Imperial Knights allies into Imperium factions
    if "Imperial Knights" in factions:
        ik_allies = [u for u in factions["Imperial Knights"].units
                     if "Imperial Knights" in u.faction_keywords]
        for name in IMPERIUM_FACTIONS:
            if name in factions:
                factions[name].units.extend(ik_allies)

    # Inject Chaos Knights allies into Chaos factions
    if "Chaos Knights" in factions:
        ck_allies = [u for u in factions["Chaos Knights"].units
                     if "Chaos Knights" in u.faction_keywords]
        for name in CHAOS_FACTIONS:
            if name in factions:
                factions[name].units.extend(ck_allies)

    # Inject Tyranid Vanguard Invaders into Genestealer Cults
    if "Tyranids" in factions and "Genestealer Cults" in factions:
        vanguard_allies = [u for u in factions["Tyranids"].units
                          if "Vanguard Invader" in u.keywords]
        factions["Genestealer Cults"].units.extend(vanguard_allies)

    # Inject Chaos Daemons into Chaos Space Marines and Chaos Knights
    if "Chaos Daemons" in factions:
        daemon_allies = [u for u in factions["Chaos Daemons"].units
                        if "Legiones Daemonica" in u.faction_keywords]
        for name in ("Chaos Space Marines", "Chaos Knights"):
            if name in factions:
                factions[name].units.extend(daemon_allies)

    # Inject generic Space Marine units into chapter factions
    if "Space Marines" in factions:
        generic_sm = [u for u in factions["Space Marines"].units
                      if u._fk_set == {"Adeptus Astartes"}]
        for name in ("Blood Angels", "Black Templars", "Space Wolves", "Dark Angels"):
            if name in factions:
                existing_names = {u.name for u in factions[name].units}
                to_inject = [u for u in generic_sm if u.name not in existing_names]
                factions[name].units.extend(to_inject)


def is_ally(unit: Unit, faction_name: str) -> bool:
    """Check if a unit is an ally based on faction_keywords."""
    faction_lower = faction_name.lower()

    if faction_lower in ("space marines", "grey knights", "adeptus custodes", "adepta sororitas",
                         "astra militarum", "adeptus mechanicus", "space wolves", "black templars",
                         "blood angels", "dark angels", "deathwatch", "imperial agents"):
        return unit.has_fk("Imperial Knights")

    if faction_lower == "chaos space marines":
        return unit.has_fk("Chaos Knights") or unit.has_fk("Cult Marines") or unit.has_fk("Legiones Daemonica")

    if faction_lower in ("chaos daemons", "thousand sons", "emperor's children", "world eaters", "death guard"):
        return unit.has_fk("Chaos Knights")

    if faction_lower == "genestealer cults":
        return unit.has_fk("Tyranids")

    if faction_lower == "drukhari":
        return unit.has_fk("Harlequins")

    if faction_lower == "imperial knights":
        return unit.has_fk("Questor Mechanicus")

    if faction_lower == "chaos knights":
        return unit.has_fk("Damned") or unit.has_fk("Legiones Daemonica")

    return False
