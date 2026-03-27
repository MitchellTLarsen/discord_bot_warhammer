"""Reusable helper utilities."""

from typing import Callable
from discord import app_commands


def parse_csv(value: str | None) -> list[str] | None:
    """Parse comma-separated string into list, returns None if empty."""
    if not value:
        return None
    result = [k.strip() for k in value.split(",") if k.strip()]
    return result or None


def build_content_lines(**kwargs: str | list[str] | None) -> str | None:
    """Build content string from labeled values.

    Args:
        **kwargs: Label=value pairs. Values can be strings, lists (joined with ', '), or None (skipped).

    Returns:
        Formatted string or None if all values are empty.
    """
    lines = []
    for label, value in kwargs.items():
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(value)
        if value:
            lines.append(f"**{label}:** {value}")
    return "\n".join(lines) if lines else None


def simple_autocomplete(
    items_getter: Callable[["ArmyCog", str | None], list[str]],
    faction_attr: str = "faction"
):
    """Factory for simple single-value autocomplete.

    Args:
        items_getter: Function(cog, faction_name) -> list of items to autocomplete
        faction_attr: Namespace attribute to get faction from (e.g., "faction", "your_faction")
    """
    async def autocomplete(self, interaction, current: str) -> list[app_commands.Choice[str]]:
        faction = getattr(interaction.namespace, faction_attr, None)
        items = items_getter(self, faction)
        if not items:
            return []
        if not current:
            return [app_commands.Choice(name=i, value=i) for i in items[:25]]
        cur = current.lower()
        return [app_commands.Choice(name=i, value=i) for i in items if cur in i.lower()][:25]
    return autocomplete


def multi_autocomplete(
    items_getter: Callable[["ArmyCog", str | None], list[str]],
    faction_attr: str = "faction"
):
    """Factory for comma-separated multi-value autocomplete.

    Args:
        items_getter: Function(cog, faction_name) -> list of items to autocomplete
        faction_attr: Namespace attribute to get faction from
    """
    async def autocomplete(self, interaction, current: str) -> list[app_commands.Choice[str]]:
        faction = getattr(interaction.namespace, faction_attr, None)
        items = items_getter(self, faction)
        if not items:
            return []

        # Parse current input for comma-separated values
        if "," in current:
            prefix = current.rsplit(",", 1)[0] + ","
            cur = current.rsplit(",", 1)[1].strip()
        else:
            prefix = ""
            cur = current

        if not cur:
            return [app_commands.Choice(name=f"{prefix}{i}".strip(), value=f"{prefix}{i}".strip()) for i in items[:25]]

        cur_lower = cur.lower()
        return [app_commands.Choice(name=f"{prefix}{i}".strip(), value=f"{prefix}{i}".strip())
                for i in items if cur_lower in i.lower()][:25]
    return autocomplete


# Type hint for the ArmyCog (avoids circular import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cogs.army import ArmyCog
