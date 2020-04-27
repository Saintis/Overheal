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

    "10929": "Renew (Rank 9)",
}

# Spell coefficients of each spell id, for determining weight of heal power
SPELL_COEFFICIENTS = {
    "10917": 0.429,
    "10916": 0.429,
    "10915": 0.429,
    "9474": 0.429,
    "9473": 0.429,
    "9472": 0.429,
    "2061": 0.429,

    "2053": 0.446,

    "25316": 0.286,
    "10961": 0.286,
    "10960": 0.286,
    "996": 0.286,
    "596": 0.286,

    "25314": 0.857,
    "10965": 0.857,
    "10964": 0.857,
    "10963": 0.857,
    "2060": 0.857,

    "6064": 0.857,
    "6063": 0.857,
    "2055": 0.857,
    "2054": 0.729,

    "27801": 0.107,
    "27805": 0.107,
    "27823": 0.107,

    "10929": 1.0 / 5,
}
