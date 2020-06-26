"""
Optimise spell casts to heal damage taken.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import numpy as np
import matplotlib.pyplot as plt

from backend import encounter_picker, shorten_spell_name
from readers import read_from_raw as raw
from damage.damage_taken import raid_damage_taken
import spell_data as sd

from simulation import CharacterData, evaluate_casting_strategy
from simulation.casting_strategy import CastingStrategy, SingleSpellStrategy


def main(argv=None):
    from backend.parser import OverhealParser

    parser = OverhealParser(need_character=True, accept_encounter=True, accept_spell_id=True, accept_spell_power=True)
    parser.add_argument("-v", "--verbose")
    parser.add_argument("--mana", type=int)

    args = parser.parse_args(argv)

    source = args.source
    encounter = args.encounter
    spell_power = args.spell_power
    mana = args.mana

    if spell_power is None or spell_power == 0:
        spell_power = 800.0

    if mana is None:
        mana = 8000.0

    lines = raw.get_lines(source)

    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, encounter)
    data = raw.get_processed_lines(encounter_lines, ref_time=encounter_start)
    events = data.all_events

    # encounter_time = (encounter_end - encounter_start).total_seconds()
    mp5 = 40.0
    mp5ooc = mp5 + 160.0
    character_data_nc = CharacterData(spell_power, 0.0, mp5, mp5ooc, mana)
    character_data_ac = CharacterData(spell_power, 1.0, mp5, mp5ooc, mana)

    times, _, deficits, name_dict, _ = raid_damage_taken(events, character_name=args.character_name)

    encounter_time = (encounter_end - encounter_start).total_seconds()
    # optimise_casts(args.character_name, times["all"], deficits, name_dict, character_data, encounter_time, spell_id=args.spell_id, verbose=args.verbose)

    talents = None

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
    sids = {}
    names = []
    lows = []
    highs = []
    path = "figs/optimise"
    for sid in sids:
        strategy = SingleSpellStrategy(talents, sid)

        nh_nc, gh_nc = evaluate_casting_strategy(
            args.character_name,
            times["all"],
            deficits,
            name_dict,
            character_data_nc,
            encounter_time,
            strategy=strategy,
            verbose=False,
            show=False,
            plot=False,
            path=path,
        )
        # nh_ac, gh_ac = evaluate_casting_strategy(
        #     args.character_name,
        #     times["all"],
        #     deficits,
        #     name_dict,
        #     character_data_ac,
        #     encounter_time,
        #     spell_id=sid,
        #     verbose=False,
        #     show=False,
        #     plot=False,
        #     path=path,
        # )

        lows.append(nh_nc)
        highs.append(gh_nc)
        names.append(strategy.name)

    # Add basic strategy as well
    strategy = CastingStrategy(talents)

    nh_nc, gh_nc = evaluate_casting_strategy(
        args.character_name,
        times["all"],
        deficits,
        name_dict,
        character_data_nc,
        encounter_time,
        strategy=strategy,
        verbose=False,
        show=False,
        plot=False,
        path=path,
    )

    lows.append(nh_nc)
    highs.append(gh_nc)
    names.append(strategy.name)

    sids = list(map(lambda s: shorten_spell_name(sd.spell_name(s)), sids))

    fig, ax = plt.subplots(figsize=(12, 8), constrained_layout=True)

    ax.bar(names, lows, color="#33cc33", label="Net heal")
    ax.bar(names, np.subtract(highs, lows), bottom=lows, color="#85e085", label="Overheal")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend()

    # add labels
    for rect, low, high in zip(ax.patches, lows, highs):
        x = rect.get_x() + rect.get_width() / 2

        y = low - 300
        ax.text(x, y, f"{low/1000:.1f}k", ha="center", va="top")

        y = high + 200
        ax.text(x, y, f"{high/1000:.1f}k", ha="center", va="bottom")

    character_data_str = str(character_data_nc)
    ax.set_title(f"Spam cast healing for {encounter}\n{character_data_str}")
    ax.set_ylabel("Net healing")
    ax.set_xlabel("Healing strategy")
    ax.tick_params(axis="x", rotation=70)

    plt.savefig(f"{path}/overview.png")
    # plt.show()

    plt.close(fig)

    print()

    h_strat, h_low = max(zip(names, lows), key=lambda x: x[1])
    print(f"  Highest healing: {h_strat} with {h_low / 1000:.1f}k healing  ({h_low / encounter_time:.1f} hps)")
    print()


if __name__ == "__main__":
    main()
