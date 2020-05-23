"""
Functions for processing raw combat logs from WoW Classic.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import re
import os
import io
from datetime import datetime

STR_P_TIME = "%m/%d %H:%M:%S.%f"


class LineProcessor:
    """Helper class for processing heal lines"""

    def __init__(self, normalise_time=False):
        self.ref_time = None

        if isinstance(normalise_time, datetime):
            self.ref_time = normalise_time
        else:
            self.normalise_time = normalise_time

    def process_line(self, line):
        p_line = process_line(line, ref_time=self.ref_time)

        if self.ref_time is None and self.normalise_time:
            self.ref_time = p_line[0]
            n_time = self.ref_time - self.ref_time
            p_line = (n_time, *p_line[1:])

        return p_line


def process_line(line, ref_time=None):
    """
    Process a matched line.

    Splits each line by ,

    Extracts spell id and name, as well as total heal and overheal values

    :param line: the line (string) to split into useful data
    :param ref_time: timestamp to reference times to
    :returns (spell id, spell name, heal, overheal, crit status)
    """
    parts = line.split(",")

    time_part = parts[0].split("  ")[0]

    time_stamp = datetime.strptime(time_part, STR_P_TIME)

    if ref_time is not None:
        time_stamp -= ref_time

    source = parts[2].split("-")[0][1:]
    target = parts[6].split("-")[0][1:]

    spell_id = parts[9]
    # spell_name = parts[10]

    total_heal = int(parts[29])
    overheal = int(parts[30])

    is_crit = ("1" in parts[32])

    return (time_stamp, source, spell_id, target, total_heal, overheal, is_crit)


def get_lines(log_file):
    """
    Load in lines from WoW Classic combat log.

    :param log_file: path to the log file
    """
    lines = ()
    try:
        fh = io.open(log_file, encoding="utf-8")
        lines = fh.readlines()
    except FileNotFoundError:
        print(f"Could not find `{log_file}`!")
        print(
            f"Looking in `{os.getcwd()}`, please double check your log file is there."
        )
        exit(1)

    return lines


def get_heals(character_name, log_lines, normalise_time=True):
    # Match logs for spell heal values
    # Does not include periodic heals such as Renew
    # Those are listed under SPELL_PERIODIC_HEAL
    heal_match = f'SPELL_HEAL,[^,]*,"{character_name}-'
    periodic_heal_match = f'SPELL_PERIODIC_HEAL,[^,]*,"{character_name}-'

    line_processor = LineProcessor(normalise_time=normalise_time)

    # Filtered and processed lines
    heal_lines = []
    periodic_lines = []
    for line in log_lines:
        if re.search(heal_match, line):
            p_line = line_processor.process_line(line)
            heal_lines.append(p_line)
        elif re.search(periodic_heal_match, line):
            p_line = line_processor.process_line(line)
            periodic_lines.append(p_line)

    return heal_lines, periodic_lines
