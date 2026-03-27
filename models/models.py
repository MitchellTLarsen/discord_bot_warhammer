"""Data models for army generation."""

from dataclasses import dataclass, field


@dataclass
class UnitOption:
    models: int
    points: int


@dataclass
class Unit:
    name: str
    options: list[UnitOption]
    is_unique: bool = False
    category: str = "other"
    url: str = ""
    keywords: list[str] = field(default_factory=list)
    faction_keywords: list[str] = field(default_factory=list)
    # Cached sets for O(1) lookup
    _kw_set: frozenset[str] = field(default_factory=frozenset, repr=False)
    _fk_set: frozenset[str] = field(default_factory=frozenset, repr=False)
    _all_kw_lower: frozenset[str] = field(default_factory=frozenset, repr=False)
    _min_points: int = 0

    def __post_init__(self):
        self._kw_set = frozenset(self.keywords)
        self._fk_set = frozenset(self.faction_keywords)
        self._all_kw_lower = frozenset(kw.lower() for kw in self.keywords + self.faction_keywords)
        self._min_points = min(opt.points for opt in self.options) if self.options else 0

    def max_count(self) -> int:
        if self.name == "Victrix Honour Guard":
            return 3
        if self.is_unique:
            return 1
        return 6 if self.category == "battleline" else 3

    def has_any_keyword(self, keywords: list[str]) -> bool:
        return any(kw.lower() in self._all_kw_lower for kw in keywords)

    def has_kw(self, kw: str) -> bool:
        return kw in self._kw_set

    def has_fk(self, fk: str) -> bool:
        return fk in self._fk_set


@dataclass
class SelectedUnit:
    unit: Unit
    option: UnitOption


@dataclass
class Enhancement:
    name: str
    points: int


@dataclass
class Detachment:
    name: str
    enhancements: list[Enhancement]


@dataclass
class FactionData:
    units: list[Unit]
    detachments: list[Detachment]
    url: str = ""
    # Pre-computed for fast autocomplete (populated by _build_indexes)
    _unit_names_sorted: list[str] = field(default_factory=list, repr=False)
    _unit_by_name_lower: dict[str, Unit] = field(default_factory=dict, repr=False)
    _keywords_sorted: list[str] = field(default_factory=list, repr=False)
    _exclude_options_sorted: list[str] = field(default_factory=list, repr=False)
    _detachment_names_sorted: list[str] = field(default_factory=list, repr=False)

    def _build_indexes(self):
        """Pre-compute indexes for fast autocomplete lookups."""
        self._unit_names_sorted = sorted({u.name for u in self.units})
        self._unit_by_name_lower = {u.name.lower(): u for u in self.units}
        self._detachment_names_sorted = sorted(d.name for d in self.detachments)

        # Keywords for bias autocomplete
        kw_set = set()
        for u in self.units:
            kw_set.update(u.keywords + u.faction_keywords)
        kw_set -= {"Battleline", "Epic Hero", "Character", ""}
        self._keywords_sorted = sorted(kw_set)

        # Exclude options = keywords + unit names
        self._exclude_options_sorted = sorted(kw_set | {u.name for u in self.units})


@dataclass
class ArmyList:
    units: list[SelectedUnit]
    detachment: Detachment | None
    enhancements: list[Enhancement]


def derive_category(name: str, keywords: list[str]) -> str:
    """Derive unit category from name and keywords."""
    if name == "Victrix Honour Guard":
        return "other"
    kw_set = set(keywords)
    if "Epic Hero" in kw_set:
        return "epic_hero"
    if "Character" in kw_set:
        return "character"
    if "Battleline" in kw_set:
        return "battleline"
    return "other"
