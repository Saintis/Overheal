"""
Collection of general functions for managing logs data.

By: Filip Gokstorp (Saintis), 2020
"""
import hashlib
from datetime import datetime
from collections import namedtuple

from readers.processor import Encounter


ENCOUNTER_START = "ENCOUNTER_START"
ENCOUNTER_END = "ENCOUNTER_END"

STR_P_TIME = "%m/%d %H:%M:%S.%f"


def anonymize_name(name):
    """Anonymize a player name"""
    name_bytes = bytes(name, "utf8")
    hash_obj = hashlib.sha1(name_bytes)

    return hash_obj.hexdigest()[:4]


def shorten_spell_name(spell_name):
    spell_name_parts = spell_name.split()
    if "[" in spell_name:
        spell_tag = spell_name_parts[1][:-1]
    elif "(" in spell_name:
        spell_tag = "".join([k[0] for k in spell_name_parts[:-2]]) + spell_name_parts[-1][:-1]
    else:
        spell_tag = "".join([k[0] for k in spell_name_parts])

    return spell_tag


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

    for event in processed_lines:
        spell_id = event.spell_id
        if filter_spell_id and spell_id != filter_spell_id:
            continue

        is_crit = event.is_crit
        if ignore_crit and is_crit:
            continue

        if spell_id not in spell_dict:
            spell_dict[spell_id] = []

        spell_dict[spell_id].append((event.total_heal, event.overheal, is_crit))

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

    encounter_boss = None
    start = 0

    for i, line in enumerate(log_lines):
        if ENCOUNTER_START in line:
            encounter_boss = line.split(",")[2].strip('"')
            start = i

        if ENCOUNTER_END in line:
            boss = line.split(",")[2].strip('"')
            if boss != encounter_boss:
                raise ValueError(f"Non-matching encounter end {encounter_boss} != {boss}")

            encounters.append(Encounter(encounter_boss, start, i + 1))

    return encounters


def select_encounter(encounters):
    print("Found the following encounters:")
    print("")

    print(f"  {0:2d})  Whole log")

    for i, e in enumerate(encounters):
        print(f"  {i+1:2d})  {e.boss}")

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
    # TODO: move this to raw reader and make similar functions for API

    if encounter is None:
        # use all lines
        str_start = log[0].split("  ")[0]
        t_start = datetime.strptime(str_start, STR_P_TIME)

        str_end = log[-1].split("  ")[0]
        t_end = datetime.strptime(str_end, STR_P_TIME)

        return log, t_start, t_end

    start = encounter.start
    end = encounter.end

    encounter_lines = log[start:end + 1]

    line_start = log[start].split("  ")[0]
    t_start = datetime.strptime(line_start, STR_P_TIME)

    line_end = log[end]
    str_end = line_end.split("  ")[0]
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


class ProgressBar:
    """Simple CLI progress bar"""

    def __init__(self, end, length=70):
        self.end = end
        self.length = length

    def render(self, progress):
        """Render the progress bar"""
        assert progress >= 0, "Progress must be positive"

        pct = progress / self.end
        n_bars = int(pct * self.length)
        bars = "=" * n_bars
        if n_bars < self.length:
            bars += ">"

        return f"[{bars:70s}]  {pct:4.0%}  {progress:8d} / {self.end:8d}"
