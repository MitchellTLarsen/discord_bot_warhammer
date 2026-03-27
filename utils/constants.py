"""Constants for army generation."""

CATEGORY_ORDER = ["epic_hero", "character", "battleline", "other"]
CATEGORY_LABELS = {
    "epic_hero": "Epic Heroes",
    "character": "Characters",
    "battleline": "Battleline",
    "other": "Other Units"
}

BIAS_MULTIPLIER = {"space marines": 10.0, "default": 3.0}

# Challenge restrictions: {challenge_name: (exclude_keywords, description, extra_rules)}
CHALLENGES = {
    "infantry_only": (["Vehicle", "Monster", "Mounted", "Cavalry", "Biker"], "Infantry Only - No vehicles, monsters, or mounts", None),
    "no_characters": (["Character", "Epic Hero"], "No Characters - Leaderless army", None),
    "vehicles_only": (["Infantry", "Monster"], "Vehicles Only - Armor up!", None),
    "cheap_units": ([], "Budget Army - No unit over 150pts", {"max_unit_points": 150}),
    "battleline_heavy": ([], "Battleline Heavy - At least 50% battleline", {"min_battleline_percent": 50}),
}

# Daemon restrictions: which daemon keywords are allowed per chaos god faction
DAEMON_RESTRICTIONS = {
    "World Eaters": {"Khorne"},
    "Thousand Sons": {"Tzeentch"},
    "Death Guard": {"Nurgle"},
    "Emperor's Children": {"Slaanesh"},
}

# Faction groupings for ally injection
IMPERIUM_FACTIONS = {
    "Space Marines", "Grey Knights", "Adeptus Custodes", "Adepta Sororitas",
    "Astra Militarum", "Adeptus Mechanicus", "Imperial Knights", "Imperial Agents"
}

CHAOS_FACTIONS = {
    "Chaos Space Marines", "Chaos Daemons", "Thousand Sons", "Emperor's Children",
    "Death Guard", "World Eaters", "Chaos Knights"
}

# Keywords that identify ally units per faction
ALLY_KEYWORDS = {
    "Space Marines": {"Adeptus Astartes"},
    "Blood Angels": {"Adeptus Astartes"},
    "Dark Angels": {"Adeptus Astartes"},
    "Space Wolves": {"Adeptus Astartes"},
    "Black Templars": {"Adeptus Astartes"},
    "Deathwatch": {"Adeptus Astartes"},
    "Imperial Knights": {"Questor Mechanicus"},
    "Chaos Knights": {"Dungeons"},
}
