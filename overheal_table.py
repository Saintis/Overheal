"""
Python script for parsing a log and calculating overheals amounts and counts.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np

import process_raw_logs as raw
from spell_data import SPELL_COEFFICIENTS, SPELL_NAMES


def group_processed_lines(processed_lines, ignore_crit, spell_id=None):
    """
    Groups processed lines by spell id.

    Returns a list, with spell id, spell name, and list of heal, overheal
    """

    id_dict = dict()
    name_dict = dict()

    filter_spell_id = spell_id

    for spell_id, spell_name, total_heal, overheal, is_crit in processed_lines:
        is_crit = True if is_crit == "1\n" else False

        if ignore_crit and is_crit:
            continue

        if filter_spell_id and spell_id != filter_spell_id:
            continue

        if spell_id not in id_dict:
            # add name to name dict
            if spell_id in SPELL_NAMES:
                stripped_name = SPELL_NAMES[spell_id]
            else:
                stripped_name = spell_name.strip('"')
                stripped_name += f" [{spell_id}]"
            name_dict[spell_id] = stripped_name
            id_dict[spell_id] = []

        id_dict[spell_id].append((int(total_heal), int(overheal), is_crit))

    return name_dict, id_dict


def print_spell_aggregate(id, name, data):
    """Prints aggregate information for single spell."""
    heals, any_overheals, half_overheals, full_overheals, amount_healed, amount_overhealed = data
    under_heals = heals - any_overheals

    print(
        f"{id:>5s}  {name:28s}  {heals:3.0f}"
        f"  {under_heals / heals:7.1%}"
        f"  {any_overheals / heals:7.1%}"
        f"  {half_overheals / heals:7.1%}"
        f"  {full_overheals / heals:7.1%}"
        f"  {amount_overhealed / amount_healed:7.1%}"
    )


def aggregate_lines(grouped_lines, spell_power=0.0):
    """Aggregates and evaluates grouped lines"""
    # heals, any OH, half OH, full OH, aH, aOH
    total_data = np.zeros(6)
    data_list = []

    for id, spell_data in grouped_lines.items():
        # heals, any OH, half OH, full OH, aH, aOH
        data = np.zeros(6)
        data[0] = len(spell_data)

        # Fail more gracefully if we are missing a coefficient
        if id in SPELL_COEFFICIENTS:
            coefficient = SPELL_COEFFICIENTS[id]
        else:
            print(f"Unknown coefficient for spell id {id}!")
            coefficient = 0

        for h, oh, crit in spell_data:
            dh = coefficient * spell_power

            if crit:
                # scale spell power differential by 1.5 if spell was a crit
                dh *= 1.5

            h = h - dh
            oh = oh - dh

            if h < 0.0:
                # could happen for heals on healing reduced players, we just ignore these for now
                continue

            if oh < 0.0:
                oh = 0.0

            # if crit:
            #     print(f"* h: {h:.1f}  oh: {oh:.1f} *")
            # else:
            #     print(f"  h: {h:.1f}  oh: {oh:.1f}")

            if oh == h:
                data[3] += 1
                data[2] += 1
                data[1] += 1
            elif oh >= 0.5 * h:
                data[2] += 1
                data[1] += 1
            elif oh > 0.0:
                data[1] += 1

            data[4] += h
            data[5] += oh

        data_list.append((id, data))
        total_data += data

    return total_data, data_list


def display_lines(names, total_data, data_list, group):
    """Print data lines for cli display"""
    if len(data_list) == 0:
        return

    print(f"{'id':>5s}  {group + ' name':28s}  {'#H':>3s}  {'No OH':>7s}  {'Any OH':>7s}  {'Half OH':>7s}  {'Full OH':>7s}  {'% OHd':>7s}")

    for id, data in data_list:
        print_spell_aggregate(id, names[id], data)

    print("-" * (5 + 2 + 28 + 2 + 3 + 2 + 7 + 2 + 7 + 2 + 7 + 2 + 7 + 2 + 7))

    group_name = "Total"
    if group:
        group_name += " " + group

    print_spell_aggregate("", group_name, total_data)


def process_log(player_name, log_file, ignore_crit=False, **kwargs):
    log_lines = raw.get_lines(log_file)
    heal_lines, periodic_lines = raw.get_heals(player_name, log_lines)

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
