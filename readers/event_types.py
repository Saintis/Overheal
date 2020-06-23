"""Event types"""

from collections import namedtuple

HealEvent = namedtuple(
    "HealEvent",
    (
        "timestamp",
        "source",
        "source_id",
        "spell_id",
        "target",
        "target_id",
        "health_pct",
        "total_heal",
        "overheal",
        "is_crit",
    ),
)

DamageTakenEvent = namedtuple(
    "DamageTakenEvent",
    (
        "timestamp",
        "source",
        "source_id",
        "spell_id",
        "target",
        "target_id",
        "health_pct",
        "total_damage",
        "mitigated",
        "overkill",
    ),
)
