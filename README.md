# Warhammer 40K Army Randomiser

A Discord bot that generates random army lists for Warhammer 40K 10th Edition.

## Features

- Generate random army lists for 23 factions
- 2000 point matched play lists with automatic ally injection
- Keyword bias for themed armies (e.g., Infantry-heavy, Monster-focused)
- Keyword exclusion to avoid certain unit types
- Challenge modes (Infantry Only, No Characters, Budget Army, etc.)
- Force-include specific units in your army
- 2-player battle mode with per-player faction/detachment selection
- Re-roll buttons with 3 attempts per army
- Export army lists to text files
- Wahapedia links for every unit
- Hot reload support for development

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/randomise` | Generate a random army list |
| `/battle` | Generate armies for two players |
| `/unit` | Look up a unit on Wahapedia |
| `/factions` | List all available factions |
| `/detachments` | List detachments and enhancements for a faction |
| `/detachment-count` | Show detachment counts for all factions |
| `/datasheet-count` | Show datasheet counts by category for all factions |
| `/reload-factions` | Reload faction data from JSON files (admin) |
| `/reload` | Hot reload the bot commands |

### Randomise Options

| Option | Description |
|--------|-------------|
| `faction` | The faction (random if not provided) |
| `detachment` | Specific detachment (random if not set) |
| `include` | Force-include units (comma-separated) |
| `bias` | Bias towards keywords (comma-separated) |
| `exclude` | Exclude keywords (comma-separated) |
| `challenge` | Apply a challenge restriction |
| `owned` | Restrict to units owned by @user |

### Battle Options

| Option | Description |
|--------|-------------|
| `opponent` | The opponent (required) |
| `points` | Points limit (default 2000) |
| `your_faction` | Your faction (random if not set) |
| `your_detachment` | Your detachment (random if not set) |
| `opponent_faction` | Opponent's faction (random if not set) |
| `opponent_detachment` | Opponent's detachment (random if not set) |
| `bias` | Bias keywords for both armies |
| `exclude` | Exclude keywords for both armies |
| `challenge` | Challenge restriction for both armies |
| `your_owned` | Restrict your army to units owned by @user |
| `opponent_owned` | Restrict opponent's army to units owned by @user |

### Challenges

- **Infantry Only** - No vehicles, monsters, or mounts
- **No Characters** - Leaderless army
- **Vehicles Only** - Armor up!
- **Budget Army** - No unit over 150pts
- **Battleline Heavy** - At least 50% battleline

### Collection-Based Armies

Use the `owned` parameter to restrict army generation to units you actually own:

```
/randomise faction:Orks owned:@YourUsername
/battle opponent:@Friend your_faction:Necrons your_owned:@You opponent_owned:@Friend
```

## Adding Your Collection

To add your collection, edit `data/collections.json`:

```json
{
  "collections": {
    "your_discord_username": {
      "Faction Name": {
        "Unit Name": 2,
        "Another Unit": 1
      }
    }
  }
}
```

### How It Works

- The key must match your **Discord username** (lowercase, e.g., `scullerz`)
- Unit quantities are in **minimum unit sizes**
- Larger unit options consume multiple minimum units

### Counting Your Units

1. Find the minimum unit size in the faction JSON (e.g., `factions/orks.json`)
2. Divide your total models by the minimum size

**Example:** You have 40 Boyz. Minimum size is 10.
- `"Boyz": 4` (40 ÷ 10 = 4 minimum units)
- Can be fielded as: 4×10, 2×20, 2×10 + 1×20, etc.

**Example:** You have 6 Meganobz. Minimum size is 2.
- `"Meganobz": 3` (6 ÷ 2 = 3 minimum units)

### Quick Reference for Common Units

| Unit Type | Typical Min Size |
|-----------|-----------------|
| Characters | 1 |
| Vehicles | 1 |
| Infantry squads | 5 or 10 |
| Swarms/Beasts | 3-6 |

## Interactive Buttons

When you generate an army, you get interactive buttons:
- **Re-roll** - Generate a new army with the same settings (3 attempts)
- **Export** - Download the army list as a .txt file

For battle mode, each player has their own Re-roll and Export buttons.

## Project Structure

```
randomiser/
├── bot.py                    # Bot entry point
├── cogs/
│   └── army.py               # Discord commands (hot reloadable)
├── models/
│   └── models.py             # Data classes (Unit, ArmyList, etc.)
├── services/
│   ├── loader.py             # Faction loading and ally injection
│   ├── generator.py          # Army generation algorithm
│   └── collections.py        # Player collection management
├── data/
│   └── collections.json      # Player-owned unit collections
├── utils/
│   ├── constants.py          # Shared constants
│   ├── formatters.py         # Output formatting (embeds, text)
│   └── helpers.py            # Reusable utilities
├── views/
│   └── army_views.py         # Discord UI components
└── factions/
    └── *.json                # Faction data files
```

## Adding/Editing Factions

Faction data is stored in JSON files in the `factions/` directory. Each file contains:
- Unit definitions with point costs, model counts, and keywords
- Detachment definitions with enhancements

Example unit structure:
```json
{
  "name": "Intercessor Squad",
  "options": [[5, 90], [10, 180]],
  "keywords": ["Infantry", "Battleline", "Tacticus"],
  "faction_keywords": ["Adeptus Astartes"]
}
```

## Ally Rules

The bot automatically handles ally injection:
- Imperial Knights into Imperium factions
- Chaos Knights into Chaos factions
- Chaos Daemons into CSM and Chaos Knights
- Tyranid Vanguard Invaders into Genestealer Cults
- Generic Space Marines into chapter factions (Blood Angels, etc.)

Point limits and restrictions are enforced per faction rules.
