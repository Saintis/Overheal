"""
Count up cast buffs and resurrections.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import spell_data as sd
from readers import read_from_raw as raw


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
    log = raw.get_lines(log_file)

    # Filtered and processed lines
    res_lines = []
    buff_lines = []
    dispel_lines = []

    for line in log:
        if "SPELL_RESURRECT" in line:
            line_data = get_line_data(line)
            res_lines.append(line_data)

        elif "SPELL_DISPEL" in line:
            line_data = get_line_data(line)
            dispel_lines.append(line_data)

        elif "SPELL_CAST_SUCCESS" in line:
            line_data = get_line_data(line)
            if line_data[0] in sd.SPELL_BUFFS:
                buff_lines.append(line_data)

    return res_lines, buff_lines, dispel_lines


def aggregate_buff_lines(res_lines, buff_lines, dispel_lines):
    """
    Aggregate buff lines into list of # casts for each spell
    """

    res_data = {}
    buff_data = {}
    dispel_data = {}

    for lines, data in zip(
        (res_lines, buff_lines, dispel_lines), (res_data, buff_data, dispel_data)
    ):
        for spell_id, spell_name, source, target in lines:
            if spell_id not in data:
                data[spell_id] = {}

            spell_dict = data[spell_id]

            if source not in spell_dict:
                spell_dict[source] = 0

            spell_dict[source] += 1

    return res_data, buff_data, dispel_data


def display_data(res_data, buff_data, dispel_data):
    all_data = (res_data, buff_data, dispel_data)
    data_names = ("Resurrections", "Buffs", "Dispels")

    for data, desc in zip(all_data, data_names):
        print(f"{desc} data:")
        for spell_id, d in data.items():
            spell_name = sd.spell_name(spell_id)
            print(f"  {spell_name}")
            for source, casts in d.items():
                print(f"    {source+':':<17s} {casts:3d}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyses logs and count up number of buffs and resurrections cast by each player.",
    )

    parser.add_argument("log_file", help="Path to the log file to analyse")

    args = parser.parse_args()

    buff_data = get_buff_lines(args.log_file)
    buff_data = aggregate_buff_lines(*buff_data)
    display_data(*buff_data)
