"""
Python script for parsing a log and calculating overheals amounts and counts.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np
import re

from spell_data import SPELL_COEFFICIENTS, SPELL_NAMES

def process_line(line):
    """
    Process a matched line.

    Splits by ,

    Extracts spell id and name, as well as total heal and overheal values
    """
    parts = line.split(",")

    spell_id = parts[9]
    spell_name = parts[10]

    total_heal = parts[29]
    overheal = parts[30]
    is_crit = parts[32]

    return (spell_id, spell_name, total_heal, overheal, is_crit)


def group_processed_lines(processed_lines, ignore_crit, spell_id=None):
    """
    Groups processed lines by spell id.

    Returns a list, with spell id, spell name, and list of heal, overheal
    """

    id_dict = dict()
    name_dict = dict()

    filter_spell_id = spell_id

    for spell_id, spell_name, total_heal, overheal, is_crit in processed_lines:
        if ignore_crit and is_crit == "1\n":
            continue

        if filter_spell_id and spell_id != filter_spell_id:
            continue

        if spell_id not in id_dict:
            # add name to name dict
            if spell_id in SPELL_NAMES:
                stripped_name = SPELL_NAMES[spell_id]
            else:
                stripped_name = spell_name.strip('"')
            name_dict[spell_id] = stripped_name
            id_dict[spell_id] = []

        id_dict[spell_id].append((int(total_heal), int(overheal)))

    return name_dict, id_dict


def print_spell_aggregate(name, data):
    """Prints aggregate information for single spell."""
    heals, any_overheals, half_overheals, full_overheals, amount_healed, amount_overhealed = data
    under_heals = heals - any_overheals

    print(
        f"{name:28s}  {heals:3.0f}"
        f"  {under_heals / heals:7.1%}"
        f"  {any_overheals / heals:7.1%}"
        f"  {half_overheals / heals:7.1%}"
        f"  {full_overheals / heals:7.1%}"
        f"  {amount_overhealed / amount_healed:7.1%}"
    )


def aggregate_lines(grouped_lines, spell_power=0):
    """Aggregates and evaluates grouped lines"""
    # heals, any OH, half OH, full OH, aH, aOH
    total_data = np.zeros(6)
    data_list = []

    for id, spell_data in grouped_lines.items():
        # heals, any OH, half OH, full OH, aH, aOH
        data = np.zeros(6)
        data[0] = len(spell_data)

        coefficient = SPELL_COEFFICIENTS[id]

        for h, oh in spell_data:
            dh = coefficient * spell_power
            h = h - dh
            oh = oh - dh

            if oh < 0.0:
                oh = 0.0

            if oh >= 0.9 * h:
                data[3] += 1
                data[2] += 1
                data[1] += 1
            elif oh >= 0.5 * h:
                data[2] += 1
                data[1] += 1
            elif oh > 0:
                data[1] += 1

            data[4] += h
            data[5] += oh

        data_list.append((id, data))
        total_data += data

    return total_data, data_list


def display_lines(names, total_data, data_list, group):
    """Print data lines for cli display"""
    print(f"{group + ' name':28s}  {'#H':>3s}  {'No OH':>7s}  {'Any OH':>7s}  {'Half OH':>7s}  {'Full OH':>7s}  {'% OHd':>7s}")

    for id, data in data_list:
        print_spell_aggregate(names[id], data)

    print("-" * (28 + 2 + 3 + 2 + 7 + 2 + 7 + 2 + 7 + 2 + 7 + 2 + 7))

    group_name = "Total"
    if group:
        group_name += " " + group

    print_spell_aggregate(group_name, total_data)


def get_lines(player_name, log_file):
    """Get the lines"""
    fh = open(log_file)
    log = fh.readlines()

    # Match logs for spell heal values
    # Does not include periodic heals such as Renew
    # Those are listed under SPELL_PERIODIC_HEAL
    heal_match = f'SPELL_HEAL,[^,]*,"{player_name}-'
    periodic_heal_match = f'SPELL_PERIODIC_HEAL,[^,]*,"{player_name}-'

    # Filtered and processed lines
    heal_lines = []
    periodic_lines = []
    for line in log:
        if re.search(heal_match, line):
            p_line = process_line(line)
            heal_lines.append(p_line)
        elif re.search(periodic_heal_match, line):
            p_line = process_line(line)
            periodic_lines.append(p_line)

    return heal_lines, periodic_lines


def process_log(player_name, log_file, ignore_crit=False, **kwargs):
    heal_lines, periodic_lines = get_lines(player_name, log_file)

    # Group lines
    names, heal_lines = group_processed_lines(heal_lines, ignore_crit)
    periodic_names, periodic_lines = group_processed_lines(periodic_lines, ignore_crit)

    # Aggregate and display data
    total_data, data_list = aggregate_lines(heal_lines, **kwargs)
    display_lines(names, total_data, data_list, "Spell")
    print("")
    total_data, data_list = aggregate_lines(periodic_lines, **kwargs)
    display_lines(periodic_names, total_data, data_list, "Periodic")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Analyses logs and count up number of overheals. Returns a list of spells and the number of recorded heals, as well as overheal frequencies.

Header explaination:
    #H: Number of heals recorded.
    No OH: Percentage of heals that had no overheal (underheals).
    Any OH: Percantage of heals that had 1 or more overheal.
    Half OH: Percentage of heals that overhealed for at least 50% of the heal value.
    Full OH: Percentage of heals that overhealed for at least 90% of the heal value.
    % OHd: Percentage of heal values that were overheal, same overheal percentage shown in WarcraftLogs. """,
    )

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument("--ignore_crit", action="store_true", help="Remove critical heals from analysis")

    args = parser.parse_args()

    process_log(args.player_name, args.log_file, ignore_crit=args.ignore_crit)
