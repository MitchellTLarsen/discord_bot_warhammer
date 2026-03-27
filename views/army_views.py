"""Discord UI views for army generation."""

import io
import logging
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from models.models import ArmyList
from services.generator import generate_army
from utils.formatters import format_army_embed, format_army_plain_text
from utils.helpers import build_content_lines

if TYPE_CHECKING:
    from cogs.army import ArmyCog

log = logging.getLogger(__name__)


class ArmyButtonView(discord.ui.View):
    """View with re-roll and export buttons for a single army."""

    def __init__(self, bot: commands.Bot, faction: str, points: int, detachment: str | None,
                 army_list: ArmyList, bias_keywords: list[str] | None = None,
                 exclude_keywords: list[str] | None = None, include_units: list[str] | None = None,
                 rerolls_left: int = 3):
        super().__init__(timeout=None)
        self.bot = bot
        self.faction = faction
        self.points = points
        self.detachment = detachment
        self.army_list = army_list
        self.bias_keywords = bias_keywords
        self.exclude_keywords = exclude_keywords
        self.include_units = include_units
        self.rerolls_left = rerolls_left

    def _get_cog(self) -> "ArmyCog | None":
        return self.bot.get_cog("ArmyCog")

    @discord.ui.button(label="Re-roll (3)", style=discord.ButtonStyle.primary, emoji="🎲")
    async def reroll_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            cog = self._get_cog()
            if not cog:
                await interaction.response.send_message("Bot is reloading, try again in a moment.", ephemeral=True)
                return
            if self.faction not in cog.factions:
                await interaction.response.send_message(f"Faction '{self.faction}' no longer available.", ephemeral=True)
                return
            if self.rerolls_left <= 0:
                await interaction.response.send_message("No re-rolls remaining!", ephemeral=True)
                return

            new_rerolls = self.rerolls_left - 1
            new_list = generate_army(cog.factions[self.faction], self.points, self.detachment,
                                    self.bias_keywords, self.exclude_keywords, self.include_units, self.faction)
            if not new_list.units:
                await interaction.response.send_message("Failed to generate army. Try different options.", ephemeral=True)
                return

            embed = format_army_embed(self.faction, cog.factions[self.faction].url, new_list)
            view = ArmyButtonView(self.bot, self.faction, self.points, self.detachment, new_list,
                                 self.bias_keywords, self.exclude_keywords, self.include_units, new_rerolls)
            view.reroll_button.label = f"Re-roll ({new_rerolls})" if new_rerolls > 0 else "No re-rolls left"
            view.reroll_button.disabled = new_rerolls <= 0

            content = build_content_lines(Include=self.include_units, Bias=self.bias_keywords, Exclude=self.exclude_keywords)
            await interaction.response.edit_message(content=content, embed=embed, view=view)
        except Exception as e:
            log.error(f"Reroll error: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message("Something went wrong during re-roll.", ephemeral=True)

    @discord.ui.button(label="Export", style=discord.ButtonStyle.secondary, emoji="📄")
    async def export_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            text = format_army_plain_text(self.faction, self.army_list)
            file = discord.File(io.BytesIO(text.encode()), filename=f"{self.faction.lower().replace(' ', '_')}_army.txt")
            await interaction.response.send_message("Here's your army list:", file=file, ephemeral=True)
        except Exception as e:
            log.error(f"Export error: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message("Failed to export army list.", ephemeral=True)


class BattleButtonView(discord.ui.View):
    """View with re-roll and export buttons for two players' armies."""

    def __init__(self, bot: commands.Bot, user1: discord.Member, user2: discord.Member,
                 faction1: str, faction2: str, army1: ArmyList, army2: ArmyList,
                 points: int, detachment1: str | None = None, detachment2: str | None = None,
                 bias_kw: list[str] | None = None, exclude_kw: list[str] | None = None,
                 challenge_desc: str | None = None, rerolls1: int = 3, rerolls2: int = 3):
        super().__init__(timeout=None)
        self.bot = bot
        self.user1, self.user2 = user1, user2
        self.faction1, self.faction2 = faction1, faction2
        self.detachment1, self.detachment2 = detachment1, detachment2
        self.army1, self.army2 = army1, army2
        self.points = points
        self.bias_kw, self.exclude_kw = bias_kw, exclude_kw
        self.challenge_desc = challenge_desc
        self.rerolls1, self.rerolls2 = rerolls1, rerolls2
        self._update_labels()

    def _get_cog(self) -> "ArmyCog | None":
        return self.bot.get_cog("ArmyCog")

    def _update_labels(self):
        self.reroll1_button.label = f"Re-roll P1 ({self.rerolls1})" if self.rerolls1 > 0 else "P1 No re-rolls"
        self.reroll1_button.disabled = self.rerolls1 <= 0
        self.reroll2_button.label = f"Re-roll P2 ({self.rerolls2})" if self.rerolls2 > 0 else "P2 No re-rolls"
        self.reroll2_button.disabled = self.rerolls2 <= 0

    def _build_content(self) -> str:
        lines = [f"**BATTLE!** {self.user1.mention} vs {self.user2.mention}", f"**Points:** {self.points}"]
        if self.challenge_desc:
            lines.append(f"**Challenge:** {self.challenge_desc}")
        if self.bias_kw:
            lines.append(f"**Bias:** {', '.join(self.bias_kw)}")
        if self.exclude_kw:
            lines.append(f"**Exclude:** {', '.join(self.exclude_kw)}")

        p1_det = f" ({self.army1.detachment.name})" if self.army1.detachment else ""
        lines.append(f"\n{self.user1.display_name}: **{self.faction1}**{p1_det}")

        p2_det = f" ({self.army2.detachment.name})" if self.army2.detachment else ""
        lines.append(f"{self.user2.display_name}: **{self.faction2}**{p2_det}")
        return "\n".join(lines)

    @discord.ui.button(label="Re-roll P1 (3)", style=discord.ButtonStyle.primary, emoji="🎲", row=0)
    async def reroll1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_reroll(interaction, 1)

    @discord.ui.button(label="Export P1", style=discord.ButtonStyle.secondary, emoji="📄", row=0)
    async def export1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = format_army_plain_text(self.faction1, self.army1)
        file = discord.File(io.BytesIO(text.encode()), filename=f"{self.faction1.lower().replace(' ', '_')}_army.txt")
        await interaction.response.send_message(f"{self.user1.display_name}'s army:", file=file, ephemeral=True)

    @discord.ui.button(label="Re-roll P2 (3)", style=discord.ButtonStyle.blurple, emoji="🎲", row=1)
    async def reroll2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_reroll(interaction, 2)

    @discord.ui.button(label="Export P2", style=discord.ButtonStyle.secondary, emoji="📄", row=1)
    async def export2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = format_army_plain_text(self.faction2, self.army2)
        file = discord.File(io.BytesIO(text.encode()), filename=f"{self.faction2.lower().replace(' ', '_')}_army.txt")
        await interaction.response.send_message(f"{self.user2.display_name}'s army:", file=file, ephemeral=True)

    async def _handle_reroll(self, interaction: discord.Interaction, player: int):
        try:
            cog = self._get_cog()
            if not cog:
                return await interaction.response.send_message("Bot is reloading, try again.", ephemeral=True)

            faction = self.faction1 if player == 1 else self.faction2
            rerolls = self.rerolls1 if player == 1 else self.rerolls2

            if rerolls <= 0:
                return await interaction.response.send_message("No re-rolls remaining!", ephemeral=True)
            if faction not in cog.factions:
                return await interaction.response.send_message(f"Faction '{faction}' no longer available.", ephemeral=True)

            detachment = self.detachment1 if player == 1 else self.detachment2
            new_army = generate_army(cog.factions[faction], self.points, detachment, self.bias_kw, self.exclude_kw, None, faction)
            if not new_army.units:
                return await interaction.response.send_message("Failed to generate army.", ephemeral=True)

            if player == 1:
                self.army1 = new_army
                self.rerolls1 -= 1
            else:
                self.army2 = new_army
                self.rerolls2 -= 1

            self._update_labels()
            embed1 = format_army_embed(self.faction1, cog.factions[self.faction1].url, self.army1)
            embed2 = format_army_embed(self.faction2, cog.factions[self.faction2].url, self.army2)
            await interaction.response.edit_message(content=self._build_content(), embeds=[embed1, embed2], view=self)
        except Exception as e:
            log.error(f"Battle reroll error: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message("Something went wrong during re-roll.", ephemeral=True)
