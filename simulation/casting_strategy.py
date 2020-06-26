"""Casting strategy"""

import spell_data as sd


class CastingStrategy:
    """
    Basic implementation of a casting strategy.

    Picks a spell and a target to cast it on.
    """

    def __init__(self, talents):
        self.talents = talents
        self.name = "Basic Strategy"

    def pick_spell(self, deficit, mana, h, **_):
        # pick spell by deficit

        choices = {
            "10917": "Flash Heal (Rank 7)",
            # "10916": "Flash Heal (Rank 6)",
            # "10915": "Flash Heal (Rank 5)",
            "9474": "Flash Heal (Rank 4)",
            # "9473": "Flash Heal (Rank 3)",
            # "9472": "Flash Heal (Rank 2)",
            # "2061": "Flash Heal (Rank 1)",

            # "2053": "Lesser Heal (Rank 3)",

            # "10965": "Greater Heal (Rank 4)",
            # "10964": "Greater Heal (Rank 3)",
            # "10963": "Greater Heal (Rank 2)",
            # "2060": "Greater Heal (Rank 1)",

            # "6064": "Heal (Rank 4)",
            # "6063": "Heal (Rank 3)",
            # "2055": "Heal (Rank 2)",
            # "2054": "Heal (Rank 1)",
        }.keys()

        # filter choices by mana available
        choices = filter(lambda sid: sd.spell_mana(sid, talents=self.talents) < mana, choices)
        # convert to healing
        heals = map(lambda sid: (sid, sd.spell_heal(sid) + sd.spell_coefficient(sid) * h), choices)

        # pick max heal with small amount of overhealing
        heals = filter(lambda x: 0.80 * x[1] < -deficit, heals)

        try:
            spell_id, heal = max(heals, key=lambda x: x[1])
        except ValueError:
            return 0, 0, 0

        mana = sd.spell_mana(spell_id)

        cast_time = 1.5 if "Flash" in sd.spell_name(spell_id) else 2.5

        return heal, mana, cast_time


class SingleSpellStrategy(CastingStrategy):
    """
    Casting strategy that only casts a signel spell by rank.
    """

    def __init__(self, talents, spell_id):
        super().__init__(talents)
        self.spell_id = spell_id
        self.name = f"Only {sd.spell_name(spell_id)}"

    def pick_spell(self, deficit, mana, h, **_):
        # pick spell by deficit
        spell_id = self.spell_id

        base_heal = sd.spell_heal(spell_id)
        coef = sd.spell_coefficient(spell_id)
        spell_mana = sd.spell_mana(spell_id, talents=self.talents)

        if spell_mana > mana:
            # print(f"{spell_mana} > {mana}")
            # could not cast
            return 0, 0, 0

        heal = base_heal + h * coef  # include random variation and crit maybe?

        cast_time = 1.5 if "Flash" in sd.spell_name(spell_id) else 2.5

        return heal, spell_mana, cast_time
