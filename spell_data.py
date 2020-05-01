"""Collection of spell names and coefficients to match spell ids."""

# Spell id to spell names, including rank
SPELL_NAMES = {
    "10917": "Flash Heal (Rank 7)",
    "10916": "Flash Heal (Rank 6)",
    "10915": "Flash Heal (Rank 5)",
    "9474": "Flash Heal (Rank 4)",
    "9473": "Flash Heal (Rank 3)",
    "9472": "Flash Heal (Rank 2)",
    "2061": "Flash Heal (Rank 1)",

    "2053": "Lesser Heal (Rank 3)",

    "25316": "Prayer of Healing (Rank 5)",
    "10961": "Prayer of Healing (Rank 4)",
    "10960": "Prayer of Healing (Rank 3)",
    "996": "Prayer of Healing (Rank 2)",
    "596": "Prayer of Healing (Rank 1)",

    "25314": "Greater Heal (Rank 5)",
    "10965": "Greater Heal (Rank 4)",
    "10964": "Greater Heal (Rank 3)",
    "10963": "Greater Heal (Rank 2)",
    "2060": "Greater Heal (Rank 1)",

    "6064": "Heal (Rank 4)",
    "6063": "Heal (Rank 3)",
    "2055": "Heal (Rank 2)",
    "2054": "Heal (Rank 1)",

    "27801": "Holy Nova (Rank 6)",
    "27805": "Holy Nova (Rank 6)",
    "27823": "Holy Nova (Rank 6)",
    "23455": "Holy Nova (Rank 1)",

    "10929": "Renew (Rank 9)",
    "6077": "Renew (Rank 5)",
    "6075": "Renew (Rank 3)",

    "19243": "Desperate Prayer (Rank 7)",
}

# Spell coefficients of each spell id, for determining weight of heal power
SPELL_COEFFICIENTS = {
    # Flash Heal
    "10917": 0.429,
    "10916": 0.429,
    "10915": 0.429,
    "9474": 0.429,
    "9473": 0.429,
    "9472": 0.429,
    "2061": 0.429,

    # Lesser Heal
    "2053": 0.446,

    # Prayer of Healing
    "25316": 0.286,
    "10961": 0.286,
    "10960": 0.286,
    "996": 0.286,
    "596": 0.286,

    # Greater Heal
    "25314": 0.857,
    "10965": 0.857,
    "10964": 0.857,
    "10963": 0.857,
    "2060": 0.857,

    # Heal
    "6064": 0.857,
    "6063": 0.857,
    "2055": 0.857,
    "2054": 0.729,

    # Holy Nova
    "27801": 0.107,
    "27805": 0.107,
    "27823": 0.107,
    "23455": 0.107,

    # Renew
    "10929": 1.0 / 5,
    "6077": 1.0 / 5,
    "6075": 1.0 / 5,

    # Desperate Prayer
    "19243": 0.429,
}

# Raw healing of each spell
SPELL_HEALS = {
    # Flash Heal
    "10917": 901.5,
    "10916": 722.5,
    "10915": 583.5,
    "9474": 453.0,
    "9473": 372.5,
    "9472": 297.0,
    "2061": 224.5,

    # Lesser Heal
    "2053": 154.0,

    # Prayer of Healing
    # "25316": 0.0,
    "10961": 965.0,
    # "10960": 0.0,
    # "996": 0.0,
    # "596": 0.0,

    # Greater Heal
    "25314": 2080.0,
    "10965": 1917.0,
    "10964": 1556.0,
    "10963": 1248.0,
    "2060": 981.5,

    # Heal
    "6064": 780.5,
    "6063": 624.0,
    "2055": 476.0,
    "2054": 330.0,

    # Holy Nova
    "27801": 326.0,
    "27805": 326.0,
    "27823": 326.0,
    "23455": 58.5,

    # Renew
    "10929": 810 / 5,
    "6077": 315 / 5,
    "6075": 175 / 5,

    # Desperate Prayer
    "19243": 1459.5,
}

def spell_name(spell_id):
    if spell_id in SPELL_NAMES:
        return SPELL_NAMES[spell_id]

    print(f"Unknown name for spell {spell_id}")
    return "Unknown"

def spell_coefficient(spell_id):
    if spell_id in SPELL_COEFFICIENTS:
        return SPELL_COEFFICIENTS[spell_id]

    print(f"Unknown coefficient for spell {spell_id}")
    return 0.0

def spell_heal(spell_id):
    if spell_id in SPELL_HEALS:
        return SPELL_HEALS[spell_id]

    print(f"Unknown base heal for spell {spell_id}")
    return 0.0
