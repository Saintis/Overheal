"""
Collection of general functions for managing logs data.

By: Filip Gokstorp (Saintis), 2020
"""
import hashlib
from datetime import datetime


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
