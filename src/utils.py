"""
Collection of general functions for managing logs data.

By: Filip Gökstorp (Saintis-Dreadmist), 2020
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
