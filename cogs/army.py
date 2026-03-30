"""Army commands cog for the Discord bot."""

import json
import logging
import random
import traceback
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from models.models import derive_category
from services.loader import load_factions
from services.generator import generate_army
from services.collections import get_player_collection
from utils.constants import CHALLENGES, CATEGORY_LABELS
from utils.formatters import format_army_embed
from utils.helpers import parse_csv, build_content_lines, simple_autocomplete, multi_autocomplete
from views.army_views import ArmyButtonView, BattleButtonView

log = logging.getLogger(__name__)


# Autocomplete item getters
def get_factions(cog, _) -> list[str]:
    return cog._faction_names_sorted

def get_detachments(cog, faction: str | None) -> list[str]:
    if not faction or faction not in cog.factions:
        return []
    return cog.factions[faction]._detachment_names_sorted

def get_keywords(cog, faction: str | None) -> list[str]:
    if not faction or faction not in cog.factions:
        return []
    return cog.factions[faction]._keywords_sorted

def get_exclude_options(cog, faction: str | None) -> list[str]:
    if not faction or faction not in cog.factions:
        return []
    return cog.factions[faction]._exclude_options_sorted

def get_unit_names(cog, faction: str | None) -> list[str]:
    if not faction or faction not in cog.factions:
        return []
    return cog.factions[faction]._unit_names_sorted


class ArmyCog(commands.Cog):
    """Cog for army generation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.factions = load_factions()
        self._faction_names_sorted = sorted(self.factions.keys())
        log.info(f"ArmyCog loaded with {len(self.factions)} factions")

    def _validate_detachment(self, faction: str, detachment: str | None) -> bool:
        """Check if detachment is valid for faction. Returns True if valid or None."""
        if not detachment:
            return True
        return any(d.name.lower() == detachment.lower() for d in self.factions[faction].detachments)

    def _apply_challenge(self, bias_kw: list[str], exclude_kw: list[str], challenge: str | None) -> tuple:
        """Apply challenge restrictions, returning (bias_kw, exclude_kw, challenge_desc, extra_rules)."""
        challenge_desc = None
        extra_rules = None
        if challenge and challenge in CHALLENGES:
            challenge_exclude, challenge_desc, extra_rules = CHALLENGES[challenge]
            exclude_kw = list(set(exclude_kw + challenge_exclude))
        return bias_kw or None, exclude_kw or None, challenge_desc, extra_rules

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for all app commands in this cog."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Command on cooldown. Try again in {error.retry_after:.1f}s", ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            log.error(f"Command error: {error}\n{traceback.format_exc()}")
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    # ==================== Autocomplete Methods (using factories) ====================

    faction_autocomplete = simple_autocomplete(get_factions)
    detachment_autocomplete = simple_autocomplete(get_detachments, "faction")
    your_detachment_autocomplete = simple_autocomplete(get_detachments, "your_faction")
    opponent_detachment_autocomplete = simple_autocomplete(get_detachments, "opponent_faction")
    unit_autocomplete = simple_autocomplete(get_unit_names, "faction")
    bias_autocomplete = multi_autocomplete(get_keywords, "faction")
    exclude_autocomplete = multi_autocomplete(get_exclude_options, "faction")
    include_autocomplete = multi_autocomplete(get_unit_names, "faction")

    # ==================== Commands ====================

    @app_commands.command(name="randomise", description="Generate a random army list")
    @app_commands.describe(
        faction="The faction (random if not provided)", points="Points limit (must be 2000)",
        detachment="Detachment (blank for random)", include="Include units (comma-separated)",
        bias="Bias keywords (comma-separated)", exclude="Exclude keywords (comma-separated)",
        challenge="Apply a challenge restriction",
        owned="Restrict to units you own (based on your Discord username)"
    )
    @app_commands.choices(challenge=[app_commands.Choice(name=v[1], value=k) for k, v in CHALLENGES.items()])
    async def randomise(self, interaction: discord.Interaction, faction: str | None = None, points: int = 2000,
                       detachment: str | None = None, include: str | None = None, bias: str | None = None,
                       exclude: str | None = None, challenge: str | None = None, owned: bool = False):
        faction_was_random = faction is None
        if faction is None:
            faction = random.choice(list(self.factions.keys()))
        elif faction not in self.factions:
            return await interaction.response.send_message(f"Unknown faction: {faction}", ephemeral=True)
        if points != 2000:
            return await interaction.response.send_message("Points must be 2000.", ephemeral=True)
        if not self._validate_detachment(faction, detachment):
            det_list = "\n".join(f"- {d.name}" for d in self.factions[faction].detachments)
            return await interaction.response.send_message(f"Unknown detachment: {detachment}\n\n**Available:**\n{det_list}", ephemeral=True)

        # Get player collection if owned=True, using Discord username
        collection = None
        owned_by = None
        if owned:
            owned_by = interaction.user.display_name
            collection = get_player_collection(owned_by, faction)
            if collection is None:
                return await interaction.response.send_message(
                    f"No collection found for '{owned_by}' with faction '{faction}'.", ephemeral=True)

        include_units = parse_csv(include)
        bias_kw, exclude_kw, challenge_desc, extra_rules = self._apply_challenge(
            parse_csv(bias) or [], parse_csv(exclude) or [], challenge
        )

        try:
            army = generate_army(self.factions[faction], points, detachment, bias_kw, exclude_kw, include_units, faction, collection)
        except Exception as e:
            log.error(f"Army generation error: {e}\n{traceback.format_exc()}")
            return await interaction.response.send_message("Failed to generate army. Please try again.", ephemeral=True)

        if extra_rules and army.units:
            if "max_unit_points" in extra_rules:
                max_pts = extra_rules["max_unit_points"]
                army.units = [u for u in army.units if u.option.points <= max_pts]

        if not army.units:
            return await interaction.response.send_message("Could not generate a valid army with those options.", ephemeral=True)

        embed = format_army_embed(faction, self.factions[faction].url, army)
        view = ArmyButtonView(self.bot, faction, points, detachment, army, bias_kw, exclude_kw, include_units,
                             faction_was_random=faction_was_random, collection=collection, owned_by=owned_by)
        content = build_content_lines(Challenge=challenge_desc, Include=include_units, Bias=bias_kw, Exclude=exclude_kw, Owned=owned_by)
        await interaction.response.send_message(content=content, embed=embed, view=view)

    @app_commands.command(name="battle", description="Generate random armies for two players")
    @app_commands.describe(
        opponent="Your opponent", points="Points limit (default 2000)",
        your_faction="Your faction (random if not set)", your_detachment="Your detachment (random if not set)",
        opponent_faction="Opponent's faction (random if not set)", opponent_detachment="Opponent's detachment (random if not set)",
        bias="Bias keywords (comma-separated)", exclude="Exclude keywords (comma-separated)",
        challenge="Apply a challenge restriction",
        your_owned="Restrict your army to units you own",
        opponent_owned="Restrict opponent's army to units they own"
    )
    @app_commands.choices(challenge=[app_commands.Choice(name=v[1], value=k) for k, v in CHALLENGES.items()])
    async def battle_command(self, interaction: discord.Interaction, opponent: discord.Member, points: int = 2000,
                            your_faction: str | None = None, your_detachment: str | None = None,
                            opponent_faction: str | None = None, opponent_detachment: str | None = None,
                            bias: str | None = None, exclude: str | None = None, challenge: str | None = None,
                            your_owned: bool = False, opponent_owned: bool = False):
        if opponent.bot:
            return await interaction.response.send_message("Can't battle a bot!", ephemeral=True)
        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("Can't battle yourself!", ephemeral=True)

        for f in (your_faction, opponent_faction):
            if f and f not in self.factions:
                return await interaction.response.send_message(f"Unknown faction: {f}", ephemeral=True)

        bias_kw, exclude_kw, challenge_desc, _ = self._apply_challenge(
            parse_csv(bias) or [], parse_csv(exclude) or [], challenge
        )

        faction1_was_random = your_faction is None
        faction2_was_random = opponent_faction is None

        faction_list = list(self.factions.keys())
        faction1 = your_faction or random.choice(faction_list)
        available_for_p2 = [f for f in faction_list if f != faction1] if not opponent_faction else faction_list
        faction2 = opponent_faction or random.choice(available_for_p2)

        if not self._validate_detachment(faction1, your_detachment):
            return await interaction.response.send_message(f"Unknown detachment for {faction1}: {your_detachment}", ephemeral=True)
        if not self._validate_detachment(faction2, opponent_detachment):
            return await interaction.response.send_message(f"Unknown detachment for {faction2}: {opponent_detachment}", ephemeral=True)

        # Get player collections if owned parameters are set (using Discord usernames)
        collection1 = None
        collection2 = None
        owned_by1 = None
        owned_by2 = None
        if your_owned:
            owned_by1 = interaction.user.display_name
            collection1 = get_player_collection(owned_by1, faction1)
            if collection1 is None:
                return await interaction.response.send_message(
                    f"No collection found for '{owned_by1}' with faction '{faction1}'.", ephemeral=True)
        if opponent_owned:
            owned_by2 = opponent.display_name
            collection2 = get_player_collection(owned_by2, faction2)
            if collection2 is None:
                return await interaction.response.send_message(
                    f"No collection found for '{owned_by2}' with faction '{faction2}'.", ephemeral=True)

        try:
            army1 = generate_army(self.factions[faction1], points, your_detachment, bias_kw, exclude_kw, None, faction1, collection1)
            army2 = generate_army(self.factions[faction2], points, opponent_detachment, bias_kw, exclude_kw, None, faction2, collection2)
        except Exception as e:
            log.error(f"Battle generation error: {e}")
            return await interaction.response.send_message("Failed to generate armies. Try again.", ephemeral=True)

        embed1 = format_army_embed(faction1, self.factions[faction1].url, army1)
        embed2 = format_army_embed(faction2, self.factions[faction2].url, army2)

        view = BattleButtonView(self.bot, interaction.user, opponent, faction1, faction2, army1, army2,
                               points, your_detachment, opponent_detachment, bias_kw, exclude_kw, challenge_desc,
                               faction1_was_random=faction1_was_random, faction2_was_random=faction2_was_random,
                               collection1=collection1, collection2=collection2,
                               owned_by1=owned_by1, owned_by2=owned_by2)
        await interaction.response.send_message(view._build_content(), embeds=[embed1, embed2], view=view)

    @app_commands.command(name="factions", description="List all available factions")
    async def factions_command(self, interaction: discord.Interaction):
        if not self.factions:
            return await interaction.response.send_message("No factions loaded. Contact an admin.", ephemeral=True)
        await interaction.response.send_message("**Available Factions:**\n" + "\n".join(f"- {n}" for n in sorted(self.factions.keys())))

    @app_commands.command(name="detachments", description="List detachments for a faction")
    @app_commands.describe(faction="The faction")
    async def detachments_command(self, interaction: discord.Interaction, faction: str):
        if faction not in self.factions:
            return await interaction.response.send_message(f"Unknown faction: {faction}", ephemeral=True)
        data = self.factions[faction]
        if not data.detachments:
            return await interaction.response.send_message(f"No detachments found for {faction}", ephemeral=True)
        lines = [f"# {faction} Detachments\n"]
        for d in sorted(data.detachments, key=lambda x: x.name):
            lines.append(f"**{d.name}**")
            for e in sorted(d.enhancements, key=lambda x: x.name):
                lines.append(f"  - {e.name} ({e.points} pts)")
            lines.append("")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="detachment-count", description="Show detachment counts for all factions")
    async def detachment_count_command(self, interaction: discord.Interaction):
        lines = ["**Detachments by Faction**\n```", f"{'Faction':<22} | Detachments", "-" * 22 + "-+-" + "-" * 11]
        for name in sorted(self.factions.keys()):
            lines.append(f"{name:<22} | {len(self.factions[name].detachments)}")
        lines.append("```")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="datasheet-count", description="Show datasheet counts for all factions (excluding allies)")
    async def datasheet_count_command(self, interaction: discord.Interaction):
        ALLY_KEYWORDS = {
            "Chaos Daemons": {"Heretic Astartes"},
            "Imperial Knights": {"Questor Mechanicus"},
            "Chaos Knights": {"Damned"},
            "Drukhari": {"Harlequins"},
        }

        counts = []
        factions_dir = Path(__file__).parent.parent / "factions"
        for path in factions_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                faction_name = data.get("faction", path.stem)
                exclude_kw = ALLY_KEYWORDS.get(faction_name, set())

                epic, char, battle, other = 0, 0, 0, 0
                for u in data.get("units", []):
                    if exclude_kw & set(u.get("faction_keywords", [])):
                        continue
                    cat = derive_category(u["name"], u.get("keywords", []))
                    if cat == "epic_hero":
                        epic += 1
                    elif cat == "character":
                        char += 1
                    elif cat == "battleline":
                        battle += 1
                    else:
                        other += 1

                total = epic + char + battle + other
                counts.append((faction_name, total, epic, char, battle, other))
            except Exception as e:
                log.error(f"Error counting datasheets in {path.name}: {e}")

        counts.sort(key=lambda x: -x[1])
        totals = [sum(c[i] for c in counts) for i in range(1, 6)]

        lines = [
            "**Datasheets by Faction** (excluding allies)\n```",
            f"{'Faction':<22} | Tot | Epic| Char| Bat | Oth",
            "-" * 22 + "-+-----+-----+-----+-----+----"
        ]
        for name, total, epic, char, battle, other in counts:
            lines.append(f"{name:<22} | {total:>3} | {epic:>3} | {char:>3} | {battle:>3} | {other:>3}")
        lines.append("-" * 22 + "-+-----+-----+-----+-----+----")
        lines.append(f"{'TOTAL':<22} | {totals[0]:>3} | {totals[1]:>3} | {totals[2]:>3} | {totals[3]:>3} | {totals[4]:>3}")
        lines.append("```")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="unit", description="Look up a unit on Wahapedia")
    @app_commands.describe(faction="The faction", unit="The unit")
    async def unit_command(self, interaction: discord.Interaction, faction: str, unit: str):
        if faction not in self.factions:
            return await interaction.response.send_message(f"Unknown faction: {faction}", ephemeral=True)

        data = self.factions[faction]
        unit_lower = unit.lower()
        found = data._unit_by_name_lower.get(unit_lower)
        if not found:
            matches = [n for n in data._unit_names_sorted if unit_lower in n.lower()]
            if len(matches) == 1:
                found = data._unit_by_name_lower[matches[0].lower()]
            elif matches:
                return await interaction.response.send_message(f"Multiple units match '{unit}':\n" + "\n".join(f"- {n}" for n in matches[:10]), ephemeral=True)
            else:
                return await interaction.response.send_message(f"Unit '{unit}' not found in {faction}.", ephemeral=True)

        opts = " | ".join(f"{o.models} models: {o.points} pts" for o in found.options)
        lines = [f"## [{found.name}]({found.url})", f"**Faction:** {faction}",
                f"**Category:** {CATEGORY_LABELS.get(found.category, found.category)}", f"**Options:** {opts}"]
        lines.append("**Unique:** Yes (max 1 per army)" if found.is_unique else f"**Max per army:** {found.max_count()}")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="reload-factions", description="Reload faction data from files (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def reload_factions_command(self, interaction: discord.Interaction):
        try:
            old_count = len(self.factions)
            self.factions = load_factions()
            self._faction_names_sorted = sorted(self.factions.keys())
            new_count = len(self.factions)
            if new_count == 0:
                await interaction.response.send_message("Warning: No factions loaded! Check logs.", ephemeral=True)
            elif new_count != old_count:
                await interaction.response.send_message(f"Reloaded factions: {old_count} → {new_count}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Reloaded {new_count} factions.", ephemeral=True)
        except Exception as e:
            log.error(f"Reload error: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message(f"Failed to reload factions: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    cog = ArmyCog(bot)
    for cmd in [cog.randomise, cog.detachments_command, cog.unit_command]:
        cmd.autocomplete("faction")(cog.faction_autocomplete)
    cog.randomise.autocomplete("detachment")(cog.detachment_autocomplete)
    cog.randomise.autocomplete("include")(cog.include_autocomplete)
    cog.randomise.autocomplete("bias")(cog.bias_autocomplete)
    cog.randomise.autocomplete("exclude")(cog.exclude_autocomplete)
    cog.unit_command.autocomplete("unit")(cog.unit_autocomplete)
    cog.battle_command.autocomplete("your_faction")(cog.faction_autocomplete)
    cog.battle_command.autocomplete("opponent_faction")(cog.faction_autocomplete)
    cog.battle_command.autocomplete("your_detachment")(cog.your_detachment_autocomplete)
    cog.battle_command.autocomplete("opponent_detachment")(cog.opponent_detachment_autocomplete)
    await bot.add_cog(cog)


async def teardown(bot: commands.Bot):
    await bot.remove_cog("ArmyCog")
