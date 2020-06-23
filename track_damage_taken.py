"""
Track damage taken

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from backend import encounter_picker
from readers import read_from_raw as raw
from damage.damage_taken import raid_damage_taken, character_damage_taken


def health_bar_chart(ax, times, deficits, health_start=0):
    deficit0 = health_start

    for t, deficit in zip(times, deficits):
        d_health = deficit - deficit0
        color = "green" if d_health > 0 else "red"

        ax.bar(t, -d_health, bottom=deficit, width=0.2, color=color)
        deficit0 = deficit


def plot_character_damage(
    times, health_pcts, deficits, nets, health_ests, encounter_time, encounter=None, character_name=None, path=None
):
    if path is None:
        path = "figs/damage"

    os.makedirs(path, exist_ok=True)

    mean_health = np.median(list(h for h in health_ests if h is not None))
    if mean_health is None or mean_health == 0:
        mean_health = 5000

    deficits = np.array(deficits, dtype=float)
    deficits /= mean_health
    deficits *= 100

    fig, (ax, ax1) = plt.subplots(2, 1, figsize=(12, 8))
    # ax_t = ax.twinx()

    health_bar_chart(ax, times, deficits, 0)
    # ax.step(times, deficits, "r", where="post", linestyle=":", linewidth=1)
    # ax.step(times, health_pcts, "b", where="post", linestyle="--", linewidth=1)
    ax.set_ylim([-101, 1])
    ax.set_xlim([0, encounter_time])
    # ax.grid()
    # ax_t.set_ylim([-100, 1])
    # ax_t.grid()
    ax.set_ylabel("Health deficit")

    if character_name and encounter:
        ax.set_title(f"{character_name} health deficit for {encounter}")
    elif character_name:
        ax.set_title(f"{character_name} health deficit")

    plt.xlabel("Encounter time [s]")

    ax1.plot(times, health_ests)
    ax1.set_xlim([0, encounter_time])

    ax1.axhline(mean_health, color="k")
    ax1.set_ylabel("Estimated health pool")

    plt.savefig(f"{path}/{character_name}_health_deficit.png")
    plt.close()

    net_damage = np.array(nets)
    net_damage[net_damage > 0] = 0
    damage_taken = np.cumsum(net_damage)

    plt.step(times, abs(damage_taken), where="post", color="red")
    plt.grid(axis="y")
    plt.gca().set_axisbelow(True)

    plt.title(f"Damage taken by {character_name} for {encounter}")
    plt.xlabel("Time [s]")
    plt.ylabel("Damage taken")
    plt.ylim((0, None))
    plt.xlim((0, None))

    plt.savefig(f"{path}/{character_name}_damage_taken.png")
    # plt.show()
    plt.close()


def plot_raid_damage(
    times,
    deficits,
    *args,
    min_deficits=None,
    character_name=None,
    deaths=None,
    resurrections=None,
    encounter=None,
    path=None,
):
    if path is None:
        path = "figs/damage"

    os.makedirs(path, exist_ok=True)

    deficits = np.array(deficits, dtype=float)

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    if len(args) == 0:
        # just one times-deficits plot
        health_bar_chart(ax, times, deficits, 0)
    else:
        assert len(args) == 2, "Need a 2nd times and a 2nd deficits array."
        ax.step(times, deficits, "r", label="Raid damage")
        ax.step(args[0], args[1], color="orange", label=f"No {character_name}")

        h_diff = np.array(args[1]) - np.array(deficits)
        ax.step(times, h_diff, "g", label="Difference")

        ax.legend()

    if min_deficits:
        ax.step(times, min_deficits, "k", where="post", linestyle="-", linewidth=1)

    if deaths is None:
        deaths = ()

    last_t = 0
    y_i = 1
    for t, _, name in deaths:
        this_t = t.total_seconds()
        ax.plot(this_t, 0, "ko")
        if this_t - last_t < 5.0:
            y_i += 1
        else:
            y_i = 1

        ax.text(this_t, 2000 * y_i, name)

        last_t = this_t

    if resurrections is None:
        resurrections = ()

    for t, _, name in resurrections:
        ax.plot(t.total_seconds(), 0, "go")
        ax.text(t.total_seconds(), 2000, name)

    if encounter:
        ax.set_title(f"Raid health deficit for {encounter}")
    else:
        ax.set_title(f"Raid health deficit")

    plt.xlabel("Encounter time [s]")
    plt.ylabel("Health deficit")

    if character_name:
        plt.savefig(f"{path}/raid_damage_no_{character_name}.png")
    else:
        plt.savefig(f"{path}/raid_damage.png")

    plt.close()


def main(argv=None):
    from backend.parser import OverhealParser

    parser = OverhealParser(accept_character=True, accept_encounter=True)
    parser.add_argument("--raid", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increases verbosity, saves health data.")
    parser.add_argument("--path")

    args = parser.parse_args(argv)

    lines = raw.get_lines(args.source)
    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, args.encounter)
    data = raw.get_processed_lines(encounter_lines, ref_time=encounter_start)
    events = data.all_events
    deaths = data.deaths
    resurrections = data.resurrections

    encounter_time = (encounter_end - encounter_start).total_seconds()

    if args.raid or args.character_name is None:
        times, deficits, _, _, min_deficits = raid_damage_taken(events, verbose=args.verbose)

        if args.character_name:
            times_nc, deficits_nc, _, _, min_deficits = raid_damage_taken(
                events, character_name=args.character_name, verbose=args.verbose
            )
        else:
            times_nc = times
            deficits_nc = deficits

        plot_raid_damage(
            times["all"],
            deficits["all"],
            times_nc["all"],
            deficits_nc["all"],
            min_deficits=min_deficits,
            character_name=args.character_name,
            encounter=encounter,
            deaths=deaths,
            resurrections=resurrections,
            path=args.path,
        )
    else:
        times, deficits, nets, health_pcts, health_ests = character_damage_taken(
            events, args.character_name, verbose=args.verbose
        )
        plot_character_damage(
            times,
            health_pcts,
            deficits,
            nets,
            health_ests,
            encounter_time,
            encounter=encounter,
            character_name=args.character_name,
            path=args.path,
        )


if __name__ == "__main__":
    main()
