"""
Optimise spell casts to heal damage taken.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
from random import random
import matplotlib.pyplot as plt

from collections import namedtuple

from backend import encounter_picker, shorten_spell_name
from readers import read_from_raw as raw
from damage.track_damage import track_raid_damage
import spell_data as sd


CharacterData = namedtuple("CharacterData", ("h", "a", "mp5", "mp5ooc", "mana"))
PendingHeal = namedtuple("PendingHeal", ("target", "heal", "mana"))


def pick_heal_target(deficits, applied_heals):
    """Simple target choosing -- healing target with largest deficit."""
    # merge in applied healing
    dd = {k: min(0, deficits.get(k, 0) + applied_heals.get(k, 0)) for k in set(deficits)}
    d = min(dd, key=dd.get)
    return d, dd[d]


def pick_spell(deficit, mana, h, spell_id=None, talents=None):
    # pick spell by deficit
    if spell_id is None:
        choices = {
            # "10917": "Flash Heal (Rank 7)",
            # "10916": "Flash Heal (Rank 6)",
            # "10915": "Flash Heal (Rank 5)",
            # "9474": "Flash Heal (Rank 4)",
            # "9473": "Flash Heal (Rank 3)",
            # "9472": "Flash Heal (Rank 2)",
            # "2061": "Flash Heal (Rank 1)",

            # "2053": "Lesser Heal (Rank 3)",

            # "10965": "Greater Heal (Rank 4)",
            # "10964": "Greater Heal (Rank 3)",
            # "10963": "Greater Heal (Rank 2)",
            # "2060": "Greater Heal (Rank 1)",

            # "6064": "Heal (Rank 4)",
            "6063": "Heal (Rank 3)",
            "2055": "Heal (Rank 2)",
            # "2054": "Heal (Rank 1)",
        }.keys()

        # filter choices by mana available
        choices = filter(lambda sid: sd.spell_mana(sid, talents=talents) < mana, choices)
        # convert to healing
        heals = map(lambda sid: (sid, sd.spell_heal(sid) + sd.spell_coefficient(sid) * h), choices)

        # pick max heal with no overhealing
        heals = filter(lambda x: x[1] < -deficit, heals)

        try:
            sid, heal = max(heals, key=lambda x: x[1])
        except ValueError:
            return 0, 0, 0

        return heal, sd.spell_mana(sid), 1.4 if "Flash" in sd.spell_name(sid) else 2.5

    base_heal = sd.spell_heal(spell_id)
    coef = sd.spell_coefficient(spell_id)
    spell_mana = sd.spell_mana(spell_id, talents=talents)

    if spell_mana > mana:
        # print(f"{spell_mana} > {mana}")
        # could not cast
        return 0, 0, 0

    heal = base_heal + h * coef  # include random variation
    cast_time = 1.5 if "Flash" in sd.spell_name(spell_id) else 2.5  # cast times for other spells

    return heal, spell_mana, cast_time


# TODO: make this a yield like function for track damage so this can be done while damage is tracked
def optimise_casts(character_name, times, deficits_time, name_dict, character_data, encounter_time, talents=None, spell_id=None, verbose=False, show=True):
    # cast heal spells and estimate their effect
    last_cast = times[0] - 5.0
    last_time = times[0]
    next_time = times[0]

    available_mana = character_data.mana
    pending_heal = None

    # dictionary of applied heals for characters
    applied_heals = dict()

    total_healing = 0
    regen_mana = 0
    casts = 0

    print()
    print(f"Optimised casts for {character_name}")

    print(f"  Mana:      {character_data.mana}")
    print(f"  +heal:     {character_data.h}")
    print(f"  mp5:       {character_data.mp5}")
    print(f"  mp5 (ooc): {character_data.mp5ooc}")

    if spell_id:
        print(f"Using {sd.spell_name(spell_id)}")

    times = iter(times)
    deficits_time = iter(deficits_time)

    deficits = next(deficits_time)
    next_deficit_time = next(times)
    last_finish_time = -5.0
    finish_time = 0.0

    ticks = []
    heals = []
    manas = []

    time_step = 0.1
    time = 0.0
    while time < encounter_time:
        if time >= finish_time:
            # process heal and/or start new heal
            if pending_heal:
                # apply heal
                target_id = pending_heal.target
                heal = pending_heal.heal
                mana = pending_heal.mana

                # do crit
                if random() < character_data.a:
                    heal *= 1.5

                applied_heal = applied_heals.get(target_id, 0)

                # heals even if target died
                deficit = min(0, deficits.get(target_id, 0) + applied_heal)
                net = min(-deficit, heal)
                applied_heals[target_id] = applied_heal + net
                pending_heal = None

                # count cast and add healing and deduct mana
                casts += 1
                total_healing += net
                available_mana -= mana

                last_finish_time = finish_time

                if verbose:
                    print(f"  {next_time:4.1f} heal {name_dict[target_id]} ({deficit: 5.0f}) for {net:4.0f}; {total_healing:5.0f}")

            # min wait time is 0.2s
            finish_time = time + time_step

            # able to cast again
            target_id, deficit = pick_heal_target(deficits, applied_heals)

            # only heal if there is someone with a deficit
            if deficit < 0:
                # pick spell by deficit
                heal, mana, cast_time = pick_spell(deficit, available_mana, character_data.h, talents=talents, spell_id=spell_id)

                if heal > 0:
                    if verbose:
                        print(f"  {next_time:4.1f} tar  {name_dict[target_id]} ({deficit: 5.0f}) for {heal:4.0f}")
                    finish_time = time + cast_time
                    pending_heal = PendingHeal(target_id, heal, mana)

        ticks.append(time)
        manas.append(available_mana)
        heals.append(total_healing)

        # get next time
        next_time = min(time + time_step, finish_time, next_deficit_time, encounter_time)
        dtime = next_time - time
        time = next_time

        # add mana for elapsed time
        if next_time - last_finish_time > 5.0:
            # ooc regen
            regen = dtime / 5 * character_data.mp5ooc
        else:
            regen = dtime / 5 * character_data.mp5

        missing_mana = character_data.mana - available_mana
        regen = min(regen, missing_mana)

        # simplify mana regen to be constant, and not in 2s batches
        available_mana += regen
        regen_mana += regen

        # update deficits if needed
        if next_time >= next_deficit_time:
            try:
                deficits = next(deficits_time)
                next_deficit_time = next(times)
            except StopIteration:
                next_deficit_time = encounter_time + time_step

    ticks.append(encounter_time)
    heals.append(total_healing)
    manas.append(available_mana)

    print()
    print(f"  Total healing: {total_healing:.0f}")
    print(f"  Casts:         {casts}")
    print(f"  CPM:           {casts / encounter_time * 60:.1f}")
    print(f"  Total hps:     {total_healing / encounter_time:.1f}")
    print(f"  Regen mana:    {regen_mana:.0f}  ({regen_mana / encounter_time * 5:.1f} mp5)")
    print(f"  End mana:      {available_mana:.0f}")

    if show:
        plt.step(ticks, heals, where="post", color="green")
        # plt.plot(heal_times, heals, "+", color="orange")

        ax = plt.twinx()
        ax.step(ticks, manas, where="post", color="blue")
        # ax.plot(ticks, manas, "+-", color="blue")
        ax.set_axisbelow(True)
        ax.grid(axis="x")

        if spell_id:
            ax.set_title(sd.spell_name(spell_id))

        plt.show()

    return total_healing


def main(argv=None):
    from backend.parser import OverhealParser

    parser = OverhealParser(need_character=True, accept_encounter=True, accept_spell_id=True)
    parser.add_argument("-v", "--verbose")
    args = parser.parse_args(argv)

    lines = raw.get_lines(args.source)

    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, args.encounter)
    data = raw.get_processed_lines(encounter_lines, ref_time=encounter_start)
    events = data.all_events

    # encounter_time = (encounter_end - encounter_start).total_seconds()
    character_data = CharacterData(800.0, 0.0, 40.0, 200.0, 8000.0)

    times, _, deficits, name_dict, _ = track_raid_damage(
        events, character_name=args.character_name
    )

    encounter_time = (encounter_end - encounter_start).total_seconds()
    # optimise_casts(args.character_name, times["all"], deficits, name_dict, character_data, encounter_time, spell_id=args.spell_id, verbose=args.verbose)

    sids = {
        "10917": "Flash Heal (Rank 7)",
        "10916": "Flash Heal (Rank 6)",
        "10915": "Flash Heal (Rank 5)",
        "9474": "Flash Heal (Rank 4)",
        "9473": "Flash Heal (Rank 3)",
        "9472": "Flash Heal (Rank 2)",
        "2061": "Flash Heal (Rank 1)",

        "2053": "Lesser Heal (Rank 3)",

        "10965": "Greater Heal (Rank 4)",
        "10964": "Greater Heal (Rank 3)",
        "10963": "Greater Heal (Rank 2)",
        "2060": "Greater Heal (Rank 1)",

        "6064": "Heal (Rank 4)",
        "6063": "Heal (Rank 3)",
        "2055": "Heal (Rank 2)",
        "2054": "Heal (Rank 1)",
    }
    ths = []
    for sid in sids:
        th = optimise_casts(args.character_name, times["all"], deficits, name_dict, character_data, encounter_time, spell_id=sid, verbose=False, show=True)
        ths.append(th)

    sids = list(map(lambda s: shorten_spell_name(sd.spell_name(s)), sids))

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.bar(sids, ths)
    ax.grid(axis="y")
    ax.set_axisbelow(True)

    # add labels
    for rect, v in zip(ax.patches, ths):
        x = rect.get_x() + rect.get_width() / 2
        y = rect.get_height() + 200

        ax.text(x, y, f"{v/1000:.1f}k", ha="center", va="bottom")

    ax.set_title(f"Spam cast healing for {encounter}")

    plt.show()


if __name__ == "__main__":
    main()
