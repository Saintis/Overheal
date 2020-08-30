"""
Analyse an encounter from the log file and plots the casts from

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
from datetime import timedelta
import matplotlib.pyplot as plt
import json

from src import readers
from src.utils import get_player_name, get_time_stamp, shorten_spell_name, anonymize_name
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


HEALERS = RAID["healers"]
TANKS = RAID["tanks"]


def get_deaths(log_lines):
    """Gets deaths in log."""

    deaths = []
    for line in log_lines:
        line_parts = line.split(",")

        if "UNIT_DIED" not in line_parts[0]:
            continue

        if "Player" not in line_parts[5]:
            continue

        timestamp = get_time_stamp(line_parts[0])
        player = get_player_name(line_parts[6])

        deaths.append((timestamp, player))

    return deaths


def plot_casts(casts_dict, encounter, mark=None, anonymize=True, deaths=None):
    casts = list(casts_dict.values())
    labels = list(casts_dict.keys())
    most_casts = max((len(c) for c in casts))

    if deaths is None:
        deaths = ()

    if anonymize:
        labels = [anonymize_name(s) for s in labels]

    w = 16
    duration = encounter.duration
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
                spell_tag = shorten_spell_name(spell_name)

                if "[" in spell_name:
                    color = "#b3b3b3" if even else "#cccccc"

                target = c[4]

                if target in TANKS:
                    color = "#99ccff" if even else "#b3d9ff"
                #     color = "#ff9999" if even else "#ffb3b3"
                elif target == "[Interrupted]":
                    color = "#ff99ff" if even else "#ffccff"
                    target = "[I]"
                elif target == "[Cancelled]":
                    color = "#ff99ff" if even else "#ffccff"
                    target = "[C]"
                elif target == "[Your target is dead]":
                    color = "#800000" if even else "#b30000"
                    target = "[TD]"
                elif target == "[Source died]":
                    color = "#800000" if even else "#b30000"
                    target = "[SD]"
                elif target == "nil":
                    target = ""

                if anonymize and target:
                    target = anonymize_name(target)

                spell_tag += "\n" + target

                w = (c[2] - c[1]).total_seconds()
                x = (c[1] - encounter.start_t).total_seconds()

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

    plt.axvline(duration, color="k")

    title = "Casts"
    if encounter:
        title += f" during {encounter.boss}"

    plt.title(title)
    plt.xlabel("Fight duration [s]")
    plt.grid(axis="x")

    if mark:
        parts = mark.split(":")
        m = int(parts[0])
        s = int(parts[1])
        plt.axvline(60 * m + s, color="k")

    last_ts = 0
    y = -1
    for timestamp, unit_id, player in deaths:
        x = timestamp.total_seconds()
        plt.axvline(x, color="k", alpha=0.5)

        if timestamp == last_ts:
            y -= 0.2
        else:
            y = -1

        plt.text(x, y, player, ha="right", va="top")
        last_ts = timestamp

    if encounter:
        e_name = encounter.short_name
    else:
        e_name = "all"

    fig_path = f"figs/casts_{e_name}.pdf"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved casts figure to `{fig_path}`")


def analyse_activity(casts_dict, encounter):
    """Analyses casting activity for each healer."""

    combat_time = encounter.duration
    print(f"Activity for {encounter.name}, {combat_time:.1f}s")

    print(f"  {'Healer':<12s}  {'setup'}  {'activ'}  {'act %'}  {'inact'}  {'regen'}")

    for healer in HEALERS:
        end = encounter.start_t

        if healer not in casts_dict:
            continue

        casts = casts_dict[healer]
        first_cast_time = casts[0][1]
        setup_time = (first_cast_time - end).total_seconds()
        end = first_cast_time

        inactive_time = 0.0
        regen_time = 0.0

        for c in casts[1:]:
            source, cast_start, cast_end, spell_id, target = c

            if cast_start < end:
                end = cast_end
                continue

            d_time = (cast_start - end).total_seconds()
            inactive_time += d_time
            if d_time > 5.0:
                regen_time += d_time - 5.0

            if cast_end == cast_start:
                end = cast_end + timedelta(seconds=1.5)
            else:
                end = cast_end

        if end < encounter.end_t:
            d_time = (encounter.end_t - end).total_seconds()
            inactive_time += d_time
            if d_time > 5.0:
                regen_time += d_time - 5.0

        active_time = combat_time - inactive_time
        active_pct = active_time / combat_time
        print(
            f"  {healer:<12s}  {setup_time:5.1f}  {active_time:5.1f}  {active_pct:5.1%}  {inactive_time:5.1f}  "
            f"{regen_time:5.1f}"
        )


def analyse_casts(source, encounter=None, all=False, **kwargs):
    processor = readers.get_processor(source)

    encounter = processor.select_encounter(encounter=encounter)
    processor.process(encounter=encounter)

    casts, _ = processor.get_casts(encounter=encounter)

    casts_dict = dict()
    for c in casts:
        s = c[0]
        if not all and s not in HEALERS:
            continue

        if s not in casts_dict:
            casts_dict[s] = []

        casts_dict[s].append(c)

    deaths = processor.deaths

    if encounter:
        # only plot casts for an encounter
        plot_casts(casts_dict, encounter, deaths=deaths, **kwargs)

    analyse_activity(casts_dict, encounter)


def main(argv=None):
    from src.parser import OverhealParser

    parser = OverhealParser(
        description="Analyses a boss encounter, or whole combat log, and characterise the amount of heal sniping going "
        "on. Only accepts WoWCombatLog.txt currently.",
        need_character=False,
        accept_encounter=True,
    )
    parser.add_argument(
        "--mark",
        help="Time-stamp to mark with a line, good for tracking important events, such as the death of a tank.",
    )
    parser.add_argument("--anonymize", action="store_true", help="Anonymizes names for distribution.")
    parser.add_argument("--all", action="store_true", help="Show all players")

    args = parser.parse_args(argv)

    analyse_casts(args.source, encounter=args.encounter, mark=args.mark, anonymize=args.anonymize, all=args.all)


if __name__ == "__main__":
    main()
