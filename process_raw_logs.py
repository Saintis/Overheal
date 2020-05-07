"""
Functions for processing raw combat logs from WoW Classic.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import re
import os
import io


def process_line(line):
    """
    Process a matched line.

    Splits each line by ,

    Extracts spell id and name, as well as total heal and overheal values

    :param line: the line (string) to split into useful data
    :returns (spell id, spell name, heal, overheal, crit status)
    """
    parts = line.split(",")

    spell_id = parts[9]
    spell_name = parts[10]

    total_heal = parts[29]
    overheal = parts[30]
    is_crit = parts[32]

    return (spell_id, spell_name, total_heal, overheal, is_crit)


def get_lines(log_file):
    """
    Load in lines from WoW Classic combat log.

    :param log_file: path to the log file
    """
    try:
        fh = io.open(log_file, encoding="utf-8")
    except FileNotFoundError:
        print(f"Could not find `{log_file}`!")
        print(
            f"Looking in `{os.getcwd()}`, please double check your log file is there."
        )
        exit(1)

    return fh.readlines()


def get_heals(character_name, log_lines):
    # Match logs for spell heal values
    # Does not include periodic heals such as Renew
    # Those are listed under SPELL_PERIODIC_HEAL
    heal_match = f'SPELL_HEAL,[^,]*,"{character_name}-'
    periodic_heal_match = f'SPELL_PERIODIC_HEAL,[^,]*,"{character_name}-'

    # Filtered and processed lines
    heal_lines = []
    periodic_lines = []
    for line in log_lines:
        if re.search(heal_match, line):
            p_line = process_line(line)
            heal_lines.append(p_line)
        elif re.search(periodic_heal_match, line):
            p_line = process_line(line)
            periodic_lines.append(p_line)

    return heal_lines, periodic_lines
