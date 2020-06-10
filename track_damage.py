"""
Track damage taken

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from backend import encounter_picker
from readers import read_from_raw as raw


def _get_net_health_change(e, current_deficit):
    """Get the net health change, accounting for mitigation, overheal and overkill."""
    gross = e[6]
    over = e[7]
    overkill = e[8]
    overheal = gross > 0 and over > 0

    if overkill < 0:
        gross -= overkill

    if gross > 0:
        # healing, then heal min of gross and current deficit
        net = min(gross, -current_deficit)
    else:
        # damage, remove mitigated damage
        net = min(gross - over, -current_deficit)

    return net, overheal, overkill


def health_bar_chart(ax, times, deficits, health_start=0):
    deficit0 = health_start

    for t, deficit in zip(times, deficits):
        d_health = deficit - deficit0
        color = "green" if d_health > 0 else "red"

        ax.bar(t, -d_health, bottom=deficit, width=0.4, color=color)
        deficit0 = deficit


def track_character_damage(events, character_name, verbose=False):
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
        health_pct = e[5]

        net, overheal, _ = _get_net_health_change(e, deficit)
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

    return times, deficits, health_pcts, health_ests


def track_raid_damage(events, character_name=None, verbose=False):
    # for each character
    times = dict(all=[])
    health_pcts = dict(all=[])
    deficits = dict(all=[])
    health_diffs = dict(all=[])
    health_ests = dict(all=[])
    deficit = dict()
    all_deficit = 0

    dead_characters = []
    death_times = {}
    min_deficit = 0
    min_deficits = []

    for e in events:
        target = e[3]
        target_id = e[4]

        if target_id not in times:
            times[target_id] = []
            health_pcts[target_id] = []
            deficits[target_id] = []
            health_diffs[target_id] = []
            health_ests[target_id] = []
            deficit[target_id] = 0

        timestamp = e[0]
        health_pct = e[5]

        current_deficit = deficit[target_id]
        net, overheal, overkill = _get_net_health_change(e, current_deficit)

        source = e[1]
        if source == character_name:
            # if character name is specified, ignore all heals from that character
            net = min(0, net)

        current_deficit += net
        all_deficit += net

        if target_id in dead_characters and timestamp > death_times[target_id]:
            print(f"Dead {target} participating again, assuming Ankh or Soulstone used.")

            dead_characters.remove(target_id)
            del death_times[target_id]

            # Recalculate min deficit
            dead_deficits = list(deficits[character_id][-1] for character_id in dead_characters)
            min_deficit = sum(dead_deficits)

        if overkill < 0:
            # someone died, lower raid min deficit
            print(f"{target} died, {current_deficit} deficit, {-overkill} overkill")
            dead_characters.append(target_id)
            death_times[target_id] = timestamp
            # print(dead_characters)

        # if (overheal and current_deficit < 0) or current_deficit > 0:
        #     print(f"{target} got overhealed with {current_deficit} deficit.")
        #     all_deficit -= current_deficit
        #     current_deficit = 0

        if current_deficit > 0:
            all_deficit -= current_deficit
            current_deficit = 0

        t = timestamp.total_seconds()

        # estimate total health from deficit and %health
        # health = max_health * %health = max_health - deficit
        # max_health * (1 - %health) = deficit
        if health_pct < 100:
            health_est = -current_deficit / (1.0 - health_pct / 100)
        else:
            health_est = None

        times[target_id].append(t)
        deficits[target_id].append(current_deficit)
        deficit[target_id] = current_deficit

        health_pcts[target_id].append(health_pct - 100)
        health_diffs[target_id].append(net)
        health_ests[target_id].append(health_est)

        times["all"].append(t)
        deficits["all"].append(all_deficit)
        health_diffs["all"].append(net)

        if verbose:
            print(t, all_deficit)

        # update min deficit
        if target_id in dead_characters:
            dead_deficits = (deficits[character_id][-1] for character_id in dead_characters)
            min_deficit = sum(dead_deficits)

        min_deficits.append(min_deficit)

    return times, deficits, min_deficits


def plot_character_damage(
    times, health_pcts, deficits, health_ests, encounter_time, encounter=None, character_name=None, path=None
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

    plt.savefig(f"{path}/{character_name}_damage.png")
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
        times, deficits, min_deficits = track_raid_damage(events, verbose=args.verbose)
        times_nc, deficits_nc, min_deficits = track_raid_damage(
            events, character_name=args.character_name, verbose=args.verbose
        )
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
        )
    else:
        times, deficits, health_pcts, health_ests = track_character_damage(
            events, args.character_name, verbose=args.verbose
        )
        plot_character_damage(
            times,
            health_pcts,
            deficits,
            health_ests,
            encounter_time,
            encounter=encounter,
            character_name=args.character_name,
        )


if __name__ == "__main__":
    main()
