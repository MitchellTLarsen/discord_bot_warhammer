"""Formatting utilities for army output."""

import discord

from models.models import ArmyList, SelectedUnit
from services.generator import group_units_by_category
from utils.constants import CATEGORY_ORDER, CATEGORY_LABELS


def _models_text(count: int) -> str:
    """Return 'X model' or 'X models'."""
    return f"{count} {'model' if count == 1 else 'models'}"


def _add_embed_fields(embed: discord.Embed, label: str, pts: int, lines: list[str]) -> None:
    """Add field(s) to embed, splitting if content exceeds 1024 chars."""
    current, length, num = [], 0, 0
    for line in lines:
        if length + len(line) + 1 > 1024 and current:
            name = f"{label} ({pts} pts)" if num == 0 else f"{label} (continued)"
            embed.add_field(name=name, value="\n".join(current), inline=False)
            current, length, num = [line], len(line) + 1, num + 1
        else:
            current.append(line)
            length += len(line) + 1
    if current:
        name = f"{label} ({pts} pts)" if num == 0 else f"{label} (continued)"
        embed.add_field(name=name, value="\n".join(current), inline=False)


def _format_unit_embed(su: SelectedUnit) -> str:
    """Format a unit for embed display."""
    return f"• [{su.unit.name}]({su.unit.url}) ({_models_text(su.option.models)}) - {su.option.points} pts"


def _format_unit_text(su: SelectedUnit) -> str:
    """Format a unit for plain text display."""
    return f"  {su.unit.name} ({_models_text(su.option.models)}) - {su.option.points} pts"


def format_army_embed(faction_name: str, faction_url: str, army_list: ArmyList) -> discord.Embed:
    """Format an army list as a Discord embed."""
    unit_pts = sum(su.option.points for su in army_list.units)
    enh_pts = sum(e.points for e in army_list.enhancements)

    embed = discord.Embed(title=faction_name.upper(), url=faction_url, color=discord.Color.gold())
    if army_list.detachment:
        embed.description = f"*Detachment: {army_list.detachment.name}*"

    if army_list.enhancements:
        lines = [f"• {e.name} - {e.points} pts" for e in sorted(army_list.enhancements, key=lambda x: x.name)]
        embed.add_field(name=f"Enhancements ({enh_pts} pts)", value="\n".join(lines), inline=False)

    grouped, allies = group_units_by_category(army_list.units, faction_name)

    for cat in CATEGORY_ORDER:
        units = grouped.get(cat, [])
        if not units:
            continue
        units = sorted(units, key=lambda su: su.unit.name)
        cat_pts = sum(su.option.points for su in units)
        lines = [_format_unit_embed(su) for su in units]
        _add_embed_fields(embed, CATEGORY_LABELS[cat], cat_pts, lines)

    if allies:
        allies = sorted(allies, key=lambda su: su.unit.name)
        ally_pts = sum(su.option.points for su in allies)
        lines = [_format_unit_embed(su) for su in allies]
        _add_embed_fields(embed, "Allies", ally_pts, lines)

    embed.set_footer(text=f"TOTAL: {unit_pts + enh_pts} pts | Units: {len(army_list.units)}")
    return embed


def format_army_plain_text(faction_name: str, army_list: ArmyList) -> str:
    """Format an army list as plain text for export."""
    unit_pts = sum(su.option.points for su in army_list.units)
    enh_pts = sum(e.points for e in army_list.enhancements)
    lines = ["=" * 50, f"  {faction_name.upper()}", "=" * 50]

    if army_list.detachment:
        lines.append(f"Detachment: {army_list.detachment.name}")
    lines.append("")

    if army_list.enhancements:
        lines.extend([f"ENHANCEMENTS ({enh_pts} pts)", "-" * 30])
        for e in sorted(army_list.enhancements, key=lambda x: x.name):
            lines.append(f"  {e.name} - {e.points} pts")
        lines.append("")

    grouped, allies = group_units_by_category(army_list.units, faction_name)

    for cat in CATEGORY_ORDER:
        units = grouped.get(cat, [])
        if not units:
            continue
        units = sorted(units, key=lambda su: su.unit.name)
        cat_pts = sum(su.option.points for su in units)
        lines.extend([f"{CATEGORY_LABELS[cat].upper()} ({cat_pts} pts)", "-" * 30])
        lines.extend(_format_unit_text(su) for su in units)
        lines.append("")

    if allies:
        allies = sorted(allies, key=lambda su: su.unit.name)
        ally_pts = sum(su.option.points for su in allies)
        lines.extend([f"ALLIES ({ally_pts} pts)", "-" * 30])
        lines.extend(_format_unit_text(su) for su in allies)
        lines.append("")

    lines.extend(["=" * 50, f"TOTAL: {unit_pts + enh_pts} pts | Units: {len(army_list.units)}", "=" * 50])
    return "\n".join(lines)
