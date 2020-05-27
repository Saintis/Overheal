"""
Analyse an encounter from the log file and plots the casts from

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
from datetime import timedelta
import matplotlib.pyplot as plt
import hashlib
import json

from readers import read_from_raw as raw
from backend.parser import OverhealParser
from backend import (
    get_player_name,
    get_time_stamp,
    list_encounters,
    select_encounter,
    lines_for_encounter,
)
import spell_data as sd


try:
    with open("raid.json") as fp:
        RAID = json.load(fp)
except FileNotFoundError:
    print(
        "Could not find raid setup file `raid.json`. Please create a file similar to `raid_example.json` with a list of"
        " your healers and tanks."
    )
    exit(400)


CANCEL_LABEL = "[c]"
HEALERS = RAID["healers"]
TANKS = RAID["tanks"]


def anonymize_name(name):
    """Anonymize a player name"""
    name_bytes = bytes(name, "utf8")
    hash_obj = hashlib.sha1(name_bytes)

    return hash_obj.hexdigest()[:4]


def get_casts(log_lines):
    """Looks for sniping in the log lines."""

    cast_list = []
    casts = dict()
    heals = []
    casting_dict = dict()

    batch_time = None
    batch_i = 0

    for line in log_lines:
        line_parts = line.split(",")

        if "Player" not in line_parts[1]:
            continue

        if "SPELL_CAST_START" in line_parts[0]:
            source = get_player_name(line_parts[2])

            spell_time = get_time_stamp(line_parts[0])
            spell_id = line_parts[9]

            casting_dict[source] = (spell_time, spell_id, line)

        elif "SPELL_CAST_SUCCESS" in line_parts[0]:
            source = get_player_name(line_parts[2])
            target = get_player_name(line_parts[6])
            success_time = get_time_stamp(line_parts[0])
            spell_id = line_parts[9]

            if source in casting_dict:
                start_time, start_id, start_line = casting_dict.pop(source)
            else:
                # instant cast
                start_time = success_time
                start_id = spell_id

            if spell_id != start_id:
                # something went weird, removing start and discounting this success
                continue

            if source not in casts:
                casts[source] = []

            cast = (source, start_time, success_time, spell_id, target)
            casts[source].append(cast)
            cast_list.append(cast)

        elif "SPELL_CAST_FAILED" in line_parts[0]:
            source = get_player_name(line_parts[2])
            cancel_time = get_time_stamp(line_parts[0])
            spell_id = line_parts[9]

            if '"Interrupted"\n' != line_parts[12]:
                # spell cast not interrupted, therefore not cancelled.
                continue

            if source in casting_dict:
                cast = casting_dict.pop(source)
                (start_time, _, _) = cast
            else:
                start_time = cancel_time

            cast = (source, start_time, cancel_time, spell_id, CANCEL_LABEL)
            cast_list.append(cast)

        elif "SPELL_HEAL" in line_parts[0]:
            heal_time = get_time_stamp(line_parts[0])
            source = get_player_name(line_parts[2])
            target = get_player_name(line_parts[6])
            spell_id = line_parts[9]

            # align with batch window
            if not batch_time or heal_time > batch_time:
                batch_time = heal_time
                batch_i = 0

            heal_amount = int(line_parts[29])  # total heal
            overheal_amount = int(line_parts[30])  # total heal
            net_heal = heal_amount - overheal_amount
            heals.append((source, heal_time, batch_i, spell_id, target, net_heal))

            batch_i += 1

    full_heal_data = []

    # match up casts and heals
    for source, heal_time, batch_i, spell_id, target, net_heal in heals:
        if source not in casts:
            continue

        for c in casts[source]:
            start_time = c[1]
            success_time = c[2]
            c_id = c[3]
            # c_target = c[4]

            if (
                c_id == spell_id
                # and c_target == target
                and success_time <= heal_time + timedelta(seconds=0.1)
            ):
                # found a match
                full_heal = (
                    source,
                    start_time,
                    success_time,
                    heal_time,
                    batch_i,
                    spell_id,
                    target,
                    net_heal,
                )
                full_heal_data.append(full_heal)

                casts[source].remove(c)

    return cast_list, full_heal_data


def plot_casts(casts, encounter=None, start=None, end=None, mark=None, anonymize=True):
    casts_dict = dict()

    for c in casts:
        s = c[0]
        if s not in HEALERS:
            continue

        if s not in casts_dict:
            casts_dict[s] = []

        casts_dict[s].append(c)

    casts = list(casts_dict.values())
    labels = list(casts_dict.keys())
    most_casts = max((len(c) for c in casts))

    if anonymize:
        labels = [anonymize_name(s) for s in labels]

    w = 16
    if end and start:
        duration = (end - start).total_seconds()
        w = duration / 4

    h = 0.6 * len(labels)
    fig = plt.figure(figsize=(w, h), constrained_layout=True)
    ax = fig.subplots(1, 1)

    for i in range(most_casts):
        even = i % 2 == 0
        widths = []
        lefts = []
        colors = []

        tags = []

        for j, cast_list in enumerate(casts):
            color = "#99ff99" if even else "#ccff99"

            if i >= len(cast_list):
                widths.append(0)
                lefts.append(0)
                colors.append(color)
            else:
                c = cast_list[i]
                spell_name = sd.spell_name(c[3], warn_on_not_found=False)
                spell_name_parts = spell_name.split()
                if "[" in spell_name:
                    spell_tag = spell_name_parts[1][:-1]
                    color = "#b3b3b3" if even else "#cccccc"
                elif "(" in spell_name:
                    spell_tag = (
                        "".join([k[0] for k in spell_name_parts[:-2]])
                        + spell_name_parts[-1][:-1]
                    )
                else:
                    spell_tag = "".join([k[0] for k in spell_name_parts])

                if start is None:
                    start = c[1]

                target = c[4]

                if target in TANKS:
                    color = "#99ccff" if even else "#b3d9ff"
                #     color = "#ff9999" if even else "#ffb3b3"
                elif target == CANCEL_LABEL:
                    color = "#ff99ff" if even else "#ffccff"
                    target = ""
                elif target == "nil":
                    target = ""

                if anonymize and target:
                    target = anonymize_name(target)

                spell_tag += "\n" + target

                w = (c[2] - c[1]).total_seconds()
                x = (c[1] - start).total_seconds()

                if w == 0:
                    # if no width, make it GCD length
                    w = 1.5

                widths.append(w)
                lefts.append(x)
                colors.append(color)

                tags.append((spell_tag, x + w / 2, j))

        ax.barh(labels, widths, left=lefts, height=0.8, color=colors)

        for tag, x, y in tags:
            ax.text(x, y, tag, ha="center", va="center")

    if end:
        x = (end - start).total_seconds()
        plt.axvline(x, color="k")

    title = "Casts"
    if encounter:
        title += " during " + encounter
    plt.title(title)
    plt.xlabel("Fight duration [s]")
    plt.grid(axis="x")

    if mark:
        parts = mark.split(":")
        m = int(parts[0])
        s = int(parts[1])
        plt.axvline(60 * m + s, color="k")

    fig_path = "figs/casts.png"
    plt.savefig(fig_path)
    print(f"Saved casts figure to `{fig_path}`")


def main(source, encounter=None, **kwargs):
    encounter_i = encounter

    log = raw.get_lines(source)

    encounters = list_encounters(log)

    if encounter_i == 0:
        encounter = None
    elif encounter_i:
        encounter = encounters[encounter_i - 1]
    else:
        encounter = select_encounter(encounters)

    encounter_lines, encounter_start, encounter_end = lines_for_encounter(
        log, encounter
    )

    casts, heals = get_casts(encounter_lines)

    plot_casts(casts, encounter, start=encounter_start, end=encounter_end, **kwargs)


if __name__ == "__main__":
    parser = OverhealParser(
        description="Analyses a boss encounter, or whole combat log, and characterise the amount of heal sniping going "
        "on. Only accepts WoWCombatLog.txt currently.",
        need_player=False,
    )

    parser.add_argument(
        "-e",
        "--encounter",
        type=int,
        help="Encounter to look at, or 0 for whole encounter. Skips selector dialogue.",
    )
    parser.add_argument(
        "--mark",
        help="Time-stamp to mark with a line, good for tracking important events, such as the death of a tank.",
    )
    parser.add_argument(
        "--anonymize", action="store_true", help="Anonymizes names for distribution."
    )

    args = parser.parse_args()

    main(**vars(args))
