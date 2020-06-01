"""
Collection of general functions for managing logs data.

By: Filip Gokstorp (Saintis), 2020
"""
from datetime import datetime, timedelta


ENCOUNTER_START = "ENCOUNTER_START"
ENCOUNTER_END = "ENCOUNTER_END"

STR_P_TIME = "%m/%d %H:%M:%S.%f"


def group_processed_lines(processed_lines, ignore_crit, spell_id=None):
    """
    Groups processed lines by spell id.

    :param processed_lines: groups lines by spell id.
    :param ignore_crit: if true, filters out crits
    :param spell_id: spell id to filter for
    :returns a dictionary by spell id, with a list of (heal, overheal, is_crit)
    """
    spell_dict = dict()

    filter_spell_id = spell_id

    for time_stamp, source, spell_id, target, total_heal, overheal, is_crit in processed_lines:
        if ignore_crit and is_crit:
            continue

        if filter_spell_id and spell_id != filter_spell_id:
            continue

        if spell_id not in spell_dict:
            spell_dict[spell_id] = []

        spell_dict[spell_id].append((total_heal, overheal, is_crit))

    return spell_dict


def get_player_name(text):
    """Converts text fragment containing a player name into just the name."""
    return text.split("-")[0].strip('"')


def get_time_stamp(text):
    """Converts raw log timestamp to datetime object"""
    return datetime.strptime(text.split("  ")[0], STR_P_TIME)


def list_encounters(log_lines):
    """List all found encounters."""
    encounters = []

    for line in log_lines:
        if ENCOUNTER_START in line:
            encounter = line.split(",")[2].strip('"')
            encounters.append(encounter)

    return encounters


def select_encounter(encounters):
    print("Found the following encounters:")
    print("")

    print(f"  {0:2d})  Whole log")

    for i, encounter in enumerate(encounters):
        print(f"  {i+1:2d})  {encounter}")

    print("")

    while True:
        i_enc = input("Encounter to analyse: ")
        try:
            i_enc = int(i_enc)

            if 0 <= i_enc <= len(encounters):
                break
        except ValueError:
            print(f"Please enter an integer between {0} and {len(encounters)}")

    if i_enc == 0:
        return None

    return encounters[i_enc - 1]


def lines_for_encounter(log, encounter):
    """Get the lines for the specified encounter."""

    if encounter is None:
        # use all lines
        str_start = log[0].split("  ")[0]
        t_start = datetime.strptime(str_start, STR_P_TIME)

        str_end = log[-1].split("  ")[0]
        t_end = datetime.strptime(str_end, STR_P_TIME)

        return log, t_start, t_end

    in_encounter = False
    encounter_lines = []
    t_start = None
    str_end = None

    for line in log:
        if ENCOUNTER_START in line and encounter in line:
            str_start = line.split("  ")[0]
            t_start = datetime.strptime(str_start, STR_P_TIME)
            in_encounter = True

        if in_encounter:
            encounter_lines.append(line)

        if ENCOUNTER_END in line and encounter in line:
            str_end = line.split("  ")[0]
            break

    if str_end is None:
        print("Did not find encounter end!")
        str_end = log[-1].split("  ")[0]

    t_end = datetime.strptime(str_end, STR_P_TIME)

    return encounter_lines, t_start, t_end


def encounter_picker(log, encounter_i=None):
    """Picks the encounter to look at"""

    encounters = list_encounters(log)

    if encounter_i == 0:
        encounter = None
    elif encounter_i:
        encounter = encounters[encounter_i - 1]
    else:
        encounter = select_encounter(encounters)

    encounter_lines, encounter_start, encounter_end = lines_for_encounter(log, encounter)
    return encounter, encounter_lines, encounter_start, encounter_end
