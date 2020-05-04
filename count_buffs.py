"""
Count up cast buffs and resurrections.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import io
import os

import numpy as np

# List of buffs / resses and their names. Used to filter buff lines
BUFF_NAMES = {
    # Priest
    "21564": "Prayer of Fortitude (Rank 2)",
    "10938": "Power Word: Fortitude (Rank 6)",

    "27681": "Prayer of Spirit (Rank 1)",
    "27841": "Divine Spirit (Rank 4)",

    "10958": "Shadow Protection (Rank 3)",

    # Mage
    "23028": "Arcane Brilliance (Rank 1)",
    "10157": "Arcane Intellect (Rank 5)",

    # Druid
    "21850": "Gift of the Wild (Rank 2)",
    "9885": "Mark of the Wild (Rank 7)",
}

RESS_NAMES = {
    # Priest
    "20770": "Resurrection (Rank 5)",
    "10881": "Resurrection (Rank 4)",

    # Druid
    "20748": "Rebirth (Rank 5)",

    # Shaman
    "20777": "Ancestral Spirit (Rank 5)",

    # Paladin
    "20773": "Redemption (Rank 5)",
}


def get_line_data(line):
    """Get data from a spell line."""
    line_parts = line.split(",")

    cast_player = line_parts[2].strip('"').split("-")[0]
    target = line_parts[6].strip('"')
    if "-" in target:
        target = target.split("-")[0]

    spell_id = line_parts[9]
    spell_name = line_parts[10]

    return (spell_id, spell_name, cast_player, target)


def get_buff_lines(log_file):
    try:
        fh = io.open(log_file, encoding="utf-8")
    except FileNotFoundError:
        print(f"Could not find `{log_file}`!")
        print(f"Looking in `{os.getcwd()}`, please double check your log file is there.")
        exit(1)

    log = fh.readlines()

    # Match logs for spell heal values
    # Does not include periodic heals such as Renew
    # Those are listed under SPELL_PERIODIC_HEAL

    # Filtered and processed lines
    res_lines = []
    buff_cast_lines = []
    buff_applied_lines = []

    for line in log:
        if "SPELL_RESURRECT" in line:
            res_lines.append(get_line_data(line))

        if "SPELL_CAST_SUCCESS" in line:
            line_data = get_line_data(line)
            if line_data[0] in BUFF_NAMES:
                buff_cast_lines.append(line_data)

        if "SPELL_AURA_APPLIED" in line:
            line_data = get_line_data(line)
            if line_data[0] in BUFF_NAMES:
                buff_applied_lines.append(line_data)

    # for line in res_lines:
    #     print("Resurrections", *line)
    #
    # for line in buff_cast_lines:
    #     print("Buff casts", *line)

    # for line in buff_applied_lines:
    #     print("Buff applied", *line)

    return res_lines, buff_cast_lines, buff_applied_lines


def aggregate_buff_lines(res_lines, buff_cast_lines, buff_applied_lines):
    """
    Aggregate buff lines into list of # casts for each spell
    """

    res_data = {}
    buff_cast_data = {}
    buff_applied_data = {}

    for lines, data in zip((res_lines, buff_cast_lines, buff_applied_lines), (res_data, buff_cast_data, buff_applied_data)):
        for spell_id, spell_name, source, target in lines:
            if spell_id not in data:
                data[spell_id] = {}

            spell_dict = data[spell_id]

            if source not in spell_dict:
                spell_dict[source] = 0

            spell_dict[source] += 1

    return res_data, buff_cast_data, buff_applied_data


def display_data(res_data, buff_cast_data, _):
    for data, desc, names in zip((res_data, buff_cast_data), ("Resurrection", "Buff cast"), (RESS_NAMES, BUFF_NAMES)):
        print(f"{desc} data:")
        for spell_id, d in data.items():
            spell_name = names[spell_id]
            print(f"  {spell_name}")
            for source, casts in d.items():
                print(f"    {source+':':<17s} {casts:3d}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
    Analyses logs and count up number of buffs and resurrections cast by each player.""",
    )

    parser.add_argument("log_file", help="Path to the log file to analyse")

    args = parser.parse_args()

    buff_data = get_buff_lines(args.log_file)
    buff_data = aggregate_buff_lines(*buff_data)
    display_data(*buff_data)
