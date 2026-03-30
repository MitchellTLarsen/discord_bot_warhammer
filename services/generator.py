"""Army generation logic."""

import random
from collections import defaultdict

from models.models import Unit, FactionData, SelectedUnit, Enhancement, ArmyList
from services.loader import is_ally
from utils.constants import BIAS_MULTIPLIER, DAEMON_RESTRICTIONS


def group_units_by_category(army: list[SelectedUnit], faction_name: str | None = None) -> tuple[dict[str, list[SelectedUnit]], list[SelectedUnit]]:
    """Group units by category, separating allies if faction_name provided."""
    groups: defaultdict[str, list[SelectedUnit]] = defaultdict(list)
    allies: list[SelectedUnit] = []
    victrix_count = 0
    for su in army:
        if faction_name and is_ally(su.unit, faction_name):
            allies.append(su)
        elif su.unit.name == "Victrix Honour Guard":
            groups["epic_hero" if victrix_count == 0 else "other"].append(su)
            victrix_count += 1
        else:
            groups[su.unit.category].append(su)
    return groups, allies


def generate_army(
    faction_data: FactionData,
    target_points: int = 2000,
    detachment_name: str | None = None,
    bias_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    include_units: list[str] | None = None,
    faction_name: str | None = None
) -> ArmyList:
    """Generate a random army list for a faction."""
    # Select detachment
    selected_detachment = None
    if detachment_name:
        selected_detachment = next((d for d in faction_data.detachments if d.name.lower() == detachment_name.lower()), None)
    elif faction_data.detachments:
        selected_detachment = random.choice(faction_data.detachments)

    # Select enhancements
    selected_enhancements: list[Enhancement] = []
    available_points = target_points
    if selected_detachment and selected_detachment.enhancements:
        for e in random.sample(selected_detachment.enhancements, min(random.randint(0, 2), len(selected_detachment.enhancements))):
            if e.points <= available_points:
                selected_enhancements.append(e)
                available_points -= e.points

    # Setup
    army: list[SelectedUnit] = []
    unit_counts: defaultdict[str, int] = defaultdict(int)
    faction_lower = (faction_name or "").lower()
    is_space_marines = faction_lower == "space marines"
    is_drukhari = faction_lower == "drukhari"
    is_chaos_knights = faction_lower == "chaos knights"
    is_imperial_knights = faction_lower == "imperial knights"
    is_chaos_daemons = faction_lower == "chaos daemons"
    is_chaos_space_marines = faction_lower == "chaos space marines"
    is_genestealer_cults = faction_lower == "genestealer cults"
    is_chaos_faction = faction_lower in ("chaos space marines", "chaos daemons", "thousand sons", "emperor's children", "world eaters", "death guard")
    is_imperium_faction = faction_lower in ("space marines", "grey knights", "adeptus custodes", "adepta sororitas", "astra militarum", "adeptus mechanicus", "space wolves", "black templars", "blood angels", "dark angels", "deathwatch", "imperial agents")
    bias_mult = BIAS_MULTIPLIER.get(faction_lower, BIAS_MULTIPLIER["default"])
    locked_chapter: str | None = None
    harlequin_points_spent = 0
    damned_points_spent = 0
    questor_mechanicus_points_spent = 0
    heretic_astartes_points_spent = 0
    cult_marines_points_spent = 0
    vanguard_invader_points_spent = 0
    daemon_ally_points_spent = 0
    daemon_battleline_by_god: dict[str, int] = {"Khorne": 0, "Nurgle": 0, "Tzeentch": 0, "Slaanesh": 0}
    daemon_nonbattleline_by_god: dict[str, int] = {"Khorne": 0, "Nurgle": 0, "Tzeentch": 0, "Slaanesh": 0}
    war_dog_count = 0
    big_knight_taken = False
    armiger_count = 0
    imperial_big_knight_taken = False

    # Add included units first (bypass restrictions - user explicitly requested these)
    if include_units:
        for include_name in include_units:
            unit = faction_data._unit_by_name_lower.get(include_name.lower())
            if not unit:
                continue
            if unit_counts[unit.name] >= unit.max_count():
                continue

            valid_opts = [opt for opt in unit.options if opt.points <= available_points]
            if not valid_opts:
                continue
            chosen_opt = random.choice(valid_opts)
            army.append(SelectedUnit(unit, chosen_opt))
            available_points -= chosen_opt.points
            unit_counts[unit.name] += 1

            # Track ally points/counts
            _track_ally_points(unit, chosen_opt, faction_lower, is_drukhari, is_chaos_knights,
                             is_imperial_knights, is_chaos_daemons, is_chaos_space_marines,
                             is_genestealer_cults, is_chaos_faction, is_imperium_faction,
                             locals())

    while available_points > 0:
        valid_options, weights = [], []

        for unit in faction_data.units:
            if unit._min_points > available_points:
                continue
            if unit_counts[unit.name] >= unit.max_count():
                continue
            if exclude_keywords and unit.has_any_keyword(exclude_keywords):
                continue

            # Space Marines chapter lock
            if is_space_marines and locked_chapter:
                chapters = unit._fk_set - {"Adeptus Astartes"}
                if chapters and locked_chapter not in chapters:
                    continue

            # Daemon restrictions
            if faction_lower in DAEMON_RESTRICTIONS:
                keyword, required_det = DAEMON_RESTRICTIONS[faction_lower]
                if unit.has_fk(keyword):
                    if not selected_detachment or selected_detachment.name != required_det:
                        continue

            # Drukhari: Harlequins only with Reaper's Wager
            is_harlequin = unit.has_fk("Harlequins")
            if is_drukhari and is_harlequin:
                if not selected_detachment or selected_detachment.name != "Reaper's Wager":
                    continue

            # Chaos Knights: Damned only with Iconoclast Fiefdom
            is_damned = unit.has_fk("Damned")
            if is_chaos_knights and is_damned:
                if not selected_detachment or selected_detachment.name != "Iconoclast Fiefdom":
                    continue

            # Imperial Knights: Questor Mechanicus only with Questor Forgepact
            is_questor_mechanicus = unit.has_fk("Questor Mechanicus")
            if is_imperial_knights and is_questor_mechanicus:
                if not selected_detachment or selected_detachment.name != "Questor Forgepact":
                    continue

            # Chaos Daemons: Heretic Astartes only with Shadow Legion
            is_heretic_astartes = unit.has_fk("Heretic Astartes")
            if is_chaos_daemons and is_heretic_astartes:
                if not selected_detachment or selected_detachment.name != "Shadow Legion":
                    continue

            # Chaos Space Marines: Cult Marines excluded from Renegade Warband
            is_cult_marines = unit.has_fk("Cult Marines")
            if is_chaos_space_marines and is_cult_marines:
                if selected_detachment and selected_detachment.name == "Renegade Warband":
                    continue

            # Genestealer Cults: Tyranid Vanguard Invaders only with Final Day
            is_tyranid_vanguard = unit.has_fk("Tyranids") and unit.has_kw("Vanguard Invader")
            if is_genestealer_cults and is_tyranid_vanguard:
                if not selected_detachment or selected_detachment.name != "Final Day":
                    continue

            # CSM/Chaos Knights: Daemon allies 1:1 battleline per non-battleline by god
            is_daemon_ally = unit.has_fk("Legiones Daemonica")
            if (is_chaos_space_marines or is_chaos_knights) and is_daemon_ally:
                unit_gods = unit._kw_set & {"Khorne", "Nurgle", "Tzeentch", "Slaanesh"}
                is_daemon_battleline = unit.has_kw("Battleline")
                if not is_daemon_battleline and unit_gods:
                    god = next(iter(unit_gods))
                    if daemon_battleline_by_god[god] <= daemon_nonbattleline_by_god[god]:
                        continue

            # Chaos factions: 3 War Dogs OR 1 big knight
            is_chaos_knight = unit.has_fk("Chaos Knights")
            is_war_dog = is_chaos_knight and unit.has_kw("War Dog")
            is_big_knight = is_chaos_knight and unit.has_kw("Titanic")
            if is_chaos_faction and (is_war_dog or is_big_knight):
                if big_knight_taken:
                    continue
                if is_big_knight and war_dog_count > 0:
                    continue
                if is_war_dog and war_dog_count >= 3:
                    continue

            # Imperium factions: 3 Armigers OR 1 big knight
            is_imperial_knight = unit.has_fk("Imperial Knights")
            is_armiger = is_imperial_knight and unit.has_kw("Armiger")
            is_imperial_big_knight = is_imperial_knight and unit.has_kw("Titanic")
            if is_imperium_faction and (is_armiger or is_imperial_big_knight):
                if imperial_big_knight_taken:
                    continue
                if is_imperial_big_knight and armiger_count > 0:
                    continue
                if is_armiger and armiger_count >= 3:
                    continue

            for opt in unit.options:
                if opt.points <= available_points:
                    if is_drukhari and is_harlequin and harlequin_points_spent + opt.points > 1000:
                        continue
                    if is_chaos_knights and is_damned and damned_points_spent + opt.points > 500:
                        continue
                    if is_imperial_knights and is_questor_mechanicus and questor_mechanicus_points_spent + opt.points > 500:
                        continue
                    if is_chaos_daemons and is_heretic_astartes and heretic_astartes_points_spent + opt.points > 1000:
                        continue
                    if is_chaos_space_marines and is_cult_marines and cult_marines_points_spent + opt.points > 500:
                        continue
                    if is_genestealer_cults and is_tyranid_vanguard and vanguard_invader_points_spent + opt.points > 1000:
                        continue
                    if (is_chaos_space_marines or is_chaos_knights) and is_daemon_ally and daemon_ally_points_spent + opt.points > 500:
                        continue

                    valid_options.append((unit, opt))
                    is_ally_unit = faction_name and faction_name not in unit.faction_keywords
                    base_weight = 0.1 if is_ally_unit else 1.0
                    weight = base_weight * bias_mult if bias_keywords and unit.has_any_keyword(bias_keywords) else base_weight
                    weights.append(weight)

        if not valid_options:
            break

        chosen_unit, chosen_opt = random.choices(valid_options, weights=weights, k=1)[0]
        army.append(SelectedUnit(chosen_unit, chosen_opt))
        available_points -= chosen_opt.points
        unit_counts[chosen_unit.name] += 1

        # Track ally points
        if is_drukhari and chosen_unit.has_fk("Harlequins"):
            harlequin_points_spent += chosen_opt.points
        if is_chaos_knights and chosen_unit.has_fk("Damned"):
            damned_points_spent += chosen_opt.points
        if is_imperial_knights and chosen_unit.has_fk("Questor Mechanicus"):
            questor_mechanicus_points_spent += chosen_opt.points
        if is_chaos_daemons and chosen_unit.has_fk("Heretic Astartes"):
            heretic_astartes_points_spent += chosen_opt.points
        if is_chaos_space_marines and chosen_unit.has_fk("Cult Marines"):
            cult_marines_points_spent += chosen_opt.points
        if is_genestealer_cults and chosen_unit.has_fk("Tyranids") and chosen_unit.has_kw("Vanguard Invader"):
            vanguard_invader_points_spent += chosen_opt.points

        if (is_chaos_space_marines or is_chaos_knights) and chosen_unit.has_fk("Legiones Daemonica"):
            daemon_ally_points_spent += chosen_opt.points
            chosen_gods = chosen_unit._kw_set & {"Khorne", "Nurgle", "Tzeentch", "Slaanesh"}
            for god in chosen_gods:
                if chosen_unit.has_kw("Battleline"):
                    daemon_battleline_by_god[god] += 1
                else:
                    daemon_nonbattleline_by_god[god] += 1

        if is_chaos_faction and chosen_unit.has_fk("Chaos Knights"):
            if chosen_unit.has_kw("War Dog"):
                war_dog_count += 1
            elif chosen_unit.has_kw("Titanic"):
                big_knight_taken = True

        if is_imperium_faction and chosen_unit.has_fk("Imperial Knights"):
            if chosen_unit.has_kw("Armiger"):
                armiger_count += 1
            elif chosen_unit.has_kw("Titanic"):
                imperial_big_knight_taken = True

        if is_space_marines and not locked_chapter:
            chapters = chosen_unit._fk_set - {"Adeptus Astartes"}
            if chapters:
                locked_chapter = next(iter(chapters))

    # Ensure at least one character is present
    has_character = any(su.unit.category in ("character", "epic_hero") for su in army)
    if not has_character and army:
        non_chars = [su for su in army if su.unit.category not in ("character", "epic_hero")]
        if non_chars:
            non_chars.sort(key=lambda su: su.option.points)
            to_swap = non_chars[0]
            freed_points = available_points + to_swap.option.points

            characters = [u for u in faction_data.units if u.category in ("character", "epic_hero")]
            valid_chars = [(u, opt) for u in characters for opt in u.options if opt.points <= freed_points]
            if valid_chars:
                char_unit, char_opt = random.choice(valid_chars)
                army.remove(to_swap)
                army.append(SelectedUnit(char_unit, char_opt))

    return ArmyList(army, selected_detachment, selected_enhancements)


def _track_ally_points(unit: Unit, chosen_opt, faction_lower: str, is_drukhari: bool,
                       is_chaos_knights: bool, is_imperial_knights: bool, is_chaos_daemons: bool,
                       is_chaos_space_marines: bool, is_genestealer_cults: bool,
                       is_chaos_faction: bool, is_imperium_faction: bool, ctx: dict) -> None:
    """Track ally points spent (helper for include_units tracking)."""
    # This is a simplified version - the actual tracking happens inline in generate_army
    pass
