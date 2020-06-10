"""
Track damage taken

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import numpy as np
import matplotlib.pyplot as plt

from backend import encounter_picker
from readers import read_from_raw as raw


def _get_net_health_change(e):
    """Get the net health change, accounting for mitigation, overheal and overkill."""
    gross = e[5]
    over = e[6]
    overkill = e[7]
    if overkill < 0:
        gross -= overkill

    return gross - over, gross > 0 and over > 0, overkill < 0


def health_bar_chart(ax, times, deficits, health_start=0):
    deficit0 = health_start

    for t, deficit in zip(times, deficits):
        d_health = deficit - deficit0
        color = "green" if d_health > 0 else "red"

        ax.bar(t, -d_health, bottom=deficit, width=0.3, color=color)
        deficit0 = deficit


def plot_character_damage(times, health_pcts, deficits, health_ests, encounter_time, encounter=None, character_name=None, path=None):
    if path is None:
        path = "figs/damage"

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
    ax.step(times, health_pcts, "b", where="post", linestyle="--", linewidth=1)
    ax.set_ylim([-101, 1])
    ax.set_xlim([0, encounter_time])
    # ax.grid()
    # ax_t.set_ylim([-100, 1])
    # ax_t.grid()

    if character_name and encounter:
        ax.set_title(f"{character_name} health deficit for {encounter}")
    elif character_name:
        ax.set_title(f"{character_name} health deficit")

    plt.xlabel("Encounter time [s]")

    ax1.plot(times, health_ests)
    ax1.set_xlim([0, encounter_time])

    ax1.axhline(mean_health, color="k")

    plt.savefig(f"{path}/{character_name}_damage.png")
    plt.close()


def plot_raid_damage(times, deficits, min_deficits, encounter=None, path=None):
    if path is None:
        path = "figs/damage"

    deficits = np.array(deficits, dtype=float)

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    health_bar_chart(ax, times, deficits, 0)
    ax.step(times, min_deficits, "k", where="post", linestyle="-", linewidth=1)

    if encounter:
        ax.set_title(f"Raid health deficit for {encounter}")
    else:
        ax.set_title(f"Raid health deficit")

    plt.xlabel("Encounter time [s]")
    plt.ylabel("Health deficit")

    plt.savefig(f"{path}/raid_damage.png")
    plt.close()


def track_character_damage(source, character_name, encounter_i=0, verbose=False, **kwargs):
    lines = raw.get_lines(source)
    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, encounter_i)

    events = raw.get_heals_and_damage(encounter_lines, ref_time=encounter_start)

    times = []
    health_pcts = []
    deficits = []
    health_diffs = []
    health_ests = []
    deficit = 0

    for e in events:
        target = e[3]
        if target != character_name:
            continue

        timestamp = e[0]
        health_pct = e[4]
        net, overheal, overkill = _get_net_health_change(e)
        net = min(net, -deficit)
        deficit += net

        if overheal:
            # overheal, at max health
            deficit = 0

        if deficit > 0:
            deficit = 0

        t = timestamp.total_seconds()

        # estimate total health from deficit and %health
        # health = max_health * %health = max_health - deficit
        # max_health * (1 - %health) = deficit
        if health_pct < 100:
            health_est = -deficit / (1.0 - health_pct / 100)
        else:
            health_est = None

        if verbose:
            print(t, deficit)

        times.append(t)
        health_pcts.append(health_pct - 100)
        deficits.append(deficit)
        health_diffs.append(net)
        health_ests.append(health_est)

    encounter_time = (encounter_end - encounter_start).total_seconds()
    plot_character_damage(times, health_pcts, deficits, health_ests, encounter_time, encounter=encounter, character_name=character_name, **kwargs)


def track_raid_damage(source, encounter_i=0, verbose=False, **kwargs):
    lines = raw.get_lines(source)
    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, encounter_i)

    events = raw.get_heals_and_damage(encounter_lines, ref_time=encounter_start)

    # for each character
    times = dict(all=[])
    health_pcts = dict(all=[])
    deficits = dict(all=[])
    health_diffs = dict(all=[])
    health_ests = dict(all=[])
    deficit = dict()
    all_deficit = 0

    dead_characters = []
    min_deficit = 0
    min_deficits = []

    for e in events:
        target = e[3]

        if target not in times:
            times[target] = []
            health_pcts[target] = []
            deficits[target] = []
            health_diffs[target] = []
            health_ests[target] = []
            deficit[target] = 0

        timestamp = e[0]
        health_pct = e[4]

        net, overheal, overkill = _get_net_health_change(e)
        net = min(net, -deficit[target])
        deficit[target] += net
        all_deficit += net

        if overheal:
            # overheal, at max health
            deficit[target] = 0

        if overkill:
            # someone died, lower raid min deficit
            dead_characters.append(target)

        if deficit[target] > 0:
            deficit[target] = 0

        t = timestamp.total_seconds()

        # estimate total health from deficit and %health
        # health = max_health * %health = max_health - deficit
        # max_health * (1 - %health) = deficit
        if health_pct < 100:
            health_est = -deficit[target] / (1.0 - health_pct / 100)
        else:
            health_est = None

        times[target].append(t)
        health_pcts[target].append(health_pct - 100)
        deficits[target].append(deficit[target])
        health_diffs[target].append(net)
        health_ests[target].append(health_est)

        times["all"].append(t)
        deficits["all"].append(all_deficit)
        health_diffs["all"].append(net)

        if verbose:
            print(t, all_deficit)

        # calculate min deficit
        min_deficit = sum((deficits[character][-1] for character in dead_characters))
        min_deficits.append(min_deficit)

    plot_raid_damage(times["all"], deficits["all"], min_deficits, encounter=encounter, **kwargs)


def main(argv=None):
    from backend.parser import OverhealParser

    parser = OverhealParser(
        need_character=True,
        accept_encounter=True
    )
    parser.add_argument("--raid", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increases verbosity, saves health data.")
    parser.add_argument("--path")

    args = parser.parse_args(argv)

    if args.raid:
        track_raid_damage(args.source, args.encounter, verbose=args.verbose, path=args.path)
    else:
        track_character_damage(args.source, args.character_name, args.encounter, verbose=args.verbose, path=args.path)


if __name__ == "__main__":
    main()
