"""
Functions for processing raw combat logs from WoW Classic.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import os
import io
from datetime import datetime

from backend import get_player_name, get_time_stamp
from .event_types import HealEvent, DamageTakenEvent

STR_P_TIME = "%m/%d %H:%M:%S.%f"


class RawProcessor:
    """Helper class for processing heal lines"""

    def __init__(self, character_name=None, normalise_time=False, include_damage=False):
        """
        :param character_name: Character name to filter for.
        """
        self.ref_time = None
        self.character_name = character_name
        self.include_damage = include_damage

        if isinstance(normalise_time, datetime):
            self.ref_time = normalise_time
        else:
            self.normalise_time = normalise_time

        self.all_events = []
        self.heals = []
        self.periodic_heals = []
        self.damage = []

        self.resurrections = []
        self.deaths = []

    def get_local_timestamp(self, part):
        """Gets local timestamp relative to start of encounter."""

        timestamp = get_time_stamp(part)

        if self.ref_time is None and self.normalise_time:
            self.ref_time = timestamp

        if self.ref_time is not None:
            timestamp -= self.ref_time

        return timestamp

    def process_lines(self, lines):
        """Process lines from raw log"""
        for line in lines:
            if "SPELL_HEAL," in line:
                self.process_heal(line, False)

            elif "SPELL_PERIODIC_HEAL," in line:
                self.process_heal(line, True)

            elif "UNIT_DIED," in line:
                self.process_resurrection_or_death(line, self.deaths)

            elif "SPELL_RESURRECT," in line:
                self.process_resurrection_or_death(line, self.resurrections)

            elif self.include_damage:
                if "SWING_DAMAGE_LANDED," in line:
                    self.process_damage(line)

                elif "SPELL_DAMAGE," in line:
                    self.process_damage(line)

                elif "SPELL_PERIODIC_DAMAGE," in line:
                    self.process_damage(line)

    def process_heal(self, line, periodic=False):
        line_parts = line.split(",")
        target_id = line_parts[5]

        if "Creature" in target_id:
            # ignore healing done by creatures
            return

        source = get_player_name(line_parts[2])
        if self.character_name and source != self.character_name:
            return

        timestamp = self.get_local_timestamp(line_parts[0])

        source_id = line_parts[1]
        source = get_player_name(line_parts[2])
        target = get_player_name(line_parts[6])

        spell_id = line_parts[9]

        health_pct = int(line_parts[14])
        gross_heal = int(line_parts[29])
        overheal = int(line_parts[30])

        is_crit = "1" in line_parts[32]

        event = HealEvent(
            timestamp, source, source_id, spell_id, target, target_id, health_pct, gross_heal, overheal, is_crit
        )

        self.all_events.append(event)
        if periodic:
            self.periodic_heals.append(event)
        else:
            self.heals.append(event)

    def process_damage(self, line):
        line_parts = line.split(",")
        target_id = line_parts[5]

        if "Creature" in target_id:
            # ignore damage done to creatures
            return

        timestamp = self.get_local_timestamp(line_parts[0])
        # source_id = line_parts[1]

        source_id = line_parts[1]
        source = get_player_name(line_parts[2])
        target = get_player_name(line_parts[6])

        if "SPELL" in line_parts[0]:
            spell_id = line_parts[9]
        else:
            spell_id = 0

        health_pct = int(line_parts[-24])
        net_damage = int(line_parts[-10])
        gross_damage = int(line_parts[-9])
        overkill = int(line_parts[-8])

        # school = line_parts[-7]
        # resisted = int(line_parts[-6])
        # blocked = int(line_parts[-5])
        # absorbed = int(line_parts[-4])
        # critical = line_parts[-3] == "1"
        # glancing = line_parts[-2] == "1"
        # crushing = line_parts[-1] == "1\n"

        mitigated = gross_damage - net_damage

        event = DamageTakenEvent(
            timestamp, source, source_id, spell_id, target, target_id, health_pct, -gross_damage, -mitigated, -overkill
        )
        self.all_events.append(event)
        self.damage.append(event)

    def process_resurrection_or_death(self, line, the_list):
        line_parts = line.split(",")

        unit_id = line_parts[5]
        if "Creature" in unit_id:
            # ignore mob and boss deaths
            return

        timestamp = self.get_local_timestamp(line_parts[0])
        name = get_player_name(line_parts[6])

        the_list.append((timestamp, unit_id, name))


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
        print(f"Looking in `{os.getcwd()}`, please double check your log file is there.")
        exit(1)

    return lines


def get_heals(log_lines, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(normalise_time=normalise_time, character_name=character_name)
    line_processor.process_lines(log_lines)

    return line_processor.heals, line_processor.periodic_heals


def get_heals_and_damage(log_lines, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(normalise_time=normalise_time, character_name=character_name, include_damage=True)
    line_processor.process_lines(log_lines)

    return line_processor.all_events


def get_processed_lines(log_lines, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(normalise_time=normalise_time, character_name=character_name, include_damage=True)
    line_processor.process_lines(log_lines)

    return line_processor
