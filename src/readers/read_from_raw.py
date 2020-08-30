"""
Functions for processing raw combat logs from WoW Classic.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import os
import io
from datetime import datetime, timedelta

from .event_types import HealEvent, DamageTakenEvent
from .processor import AbstractProcessor, Encounter

from ..utils import get_player_name, get_time_stamp

ENCOUNTER_START = "ENCOUNTER_START"
ENCOUNTER_END = "ENCOUNTER_END"
STR_P_TIME = "%m/%d %H:%M:%S.%f"


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


class RawProcessor(AbstractProcessor):
    """Helper class for processing heal lines"""

    def __init__(self, source, character_name=None, normalise_time=False, include_damage=False):
        """
        :param character_name: Character name to filter for.
        """
        super(RawProcessor, self).__init__(source, character_name)

        self.ref_time = None
        self.include_damage = include_damage

        if isinstance(normalise_time, datetime):
            self.ref_time = normalise_time
        else:
            self.normalise_time = normalise_time

        self.log_lines = get_lines(source)

    def get_local_timestamp(self, part):
        """Gets local timestamp relative to start of encounter."""

        timestamp = get_time_stamp(part)

        if self.ref_time is None and self.normalise_time:
            self.ref_time = timestamp

        if self.ref_time is not None:
            timestamp -= self.ref_time

        return timestamp

    def process(self, start=None, end=None, encounter=None):
        """
        Process lines from raw log.

        Use start and end to limit log to specific encounters. Start and end are line numbers.
        """
        if isinstance(encounter, Encounter):
            start = encounter.start if start is None else start
            end = encounter.end if end is None else end
            self.ref_time = encounter.start_t

        if start is None:
            start = 0
        if end is None:
            end = -1

        lines = self.log_lines[start:end]

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

    def get_deaths(self):
        """Gets deaths in log."""
        for line in self.log_lines:
            line_parts = line.split(",")

            if "UNIT_DIED" not in line_parts[0]:
                continue

            unit_id = line_parts[5]
            if "Creature" in line_parts[5]:
                continue

            timestamp = get_time_stamp(line_parts[0])
            player = get_player_name(line_parts[6])

            self.deaths.append((timestamp, unit_id, player))

        return self.deaths

    def get_encounters(self):
        encounters = []
        encounter_boss = None
        start = 0
        start_t = None

        for i, line in enumerate(self.log_lines):
            if ENCOUNTER_START in line:
                line_parts = line.split(",")
                encounter_boss = line_parts[2].strip('"')
                start_t = get_time_stamp(line_parts[0])
                start = i

            if ENCOUNTER_END in line:
                line_parts = line.split(",")
                boss = line_parts[2].strip('"')
                end_t = get_time_stamp(line_parts[0])

                if boss != encounter_boss:
                    raise ValueError(f"Non-matching encounter end {encounter_boss} != {boss}")

                encounters.append(Encounter(encounter_boss, start, i, start_t, end_t))

        # make "all" encounter
        start = encounters[0].start
        start_t = encounters[0].start_t
        end = encounters[-1].end
        end_t = encounters[-1].end_t
        self.all_encounters = Encounter("Whole encounter", start, end, start_t, end_t)

        return encounters

    def get_casts(self, encounter=None):
        """Get casts from a raw log"""
        if encounter is None:
            start = 0
            end = -1
        else:
            start = encounter.start
            end = encounter.end
            self.ref_time = encounter.start_t

        lines = self.log_lines[start:end]

        cast_list = []
        casts = dict()
        heals = []
        casting_dict = dict()

        batch_time = None
        batch_i = 0

        for i, line in enumerate(lines):
            line_parts = line.split(",")

            if "Player" not in line_parts[1]:
                # check for UNIT DIED
                if "UNIT_DIED" in line_parts[0]:
                    cancel_time = get_time_stamp(line_parts[0])
                    target = get_player_name(line_parts[6])

                    if target not in casting_dict:
                        continue

                    cast = casting_dict.pop(target)
                    (start_time, spell_id, _) = cast

                    cast = (target, start_time, cancel_time, spell_id, f"[Source died]")
                    cast_list.append(cast)

                continue

            if "SPELL_CAST_START" in line_parts[0]:
                source = get_player_name(line_parts[2])

                spell_time = get_time_stamp(line_parts[0])
                spell_id = line_parts[9]

                if source in casting_dict:
                    # already casting a spell
                    cast = casting_dict.pop(source)
                    (start_time, sid, _) = cast

                    # scan forward to see if cast success got batched
                    spell_complete = None
                    j = i
                    while True:
                        j += 1
                        next_line = lines[j]
                        nlp = next_line.split(",")
                        n_timestamp = get_time_stamp(nlp[0])
                        if n_timestamp > spell_time:
                            break

                        if "SPELL_CAST_SUCCESS" not in nlp[0]:
                            continue

                        n_source = get_player_name(nlp[2])
                        if n_source != source:
                            continue

                        n_sid = nlp[9]
                        if sid != n_sid:
                            continue

                        # same source and sid, spell was completed
                        target = get_player_name(nlp[6])
                        spell_complete = target
                        break

                    if spell_complete is not None:
                        cast = (source, start_time, spell_time, sid, spell_complete)
                    else:
                        cast = (source, start_time, spell_time, sid, f"[Cancelled]")

                    cast_list.append(cast)

                casting_dict[source] = (spell_time, spell_id, line)

            elif "SPELL_CAST_SUCCESS" in line_parts[0]:
                source = get_player_name(line_parts[2])
                target = get_player_name(line_parts[6])
                success_time = get_time_stamp(line_parts[0])
                spell_id = line_parts[9]

                if source in casting_dict:
                    start_time, start_id, start_line = casting_dict.pop(source)

                    if spell_id != start_id:
                        if start_time == success_time:
                            # start and success batched, ignore this success and add start back
                            casting_dict[source] = (start_time, start_id, start_line)
                            continue

                        # spell was cancelled with an instant effect
                        cast = (source, start_time, success_time, start_id, f"[Cancelled]")
                        cast_list.append(cast)

                else:
                    # instant cast
                    start_time = success_time

                if source not in casts:
                    casts[source] = []

                cast = (source, start_time, success_time, spell_id, target)
                casts[source].append(cast)
                cast_list.append(cast)

            elif "SPELL_CAST_FAILED" in line_parts[0]:
                source = get_player_name(line_parts[2])
                cancel_time = get_time_stamp(line_parts[0])
                spell_id = line_parts[9]
                reason = line_parts[12].strip('"\n')

                if reason not in ("Interrupted", "Your target is dead"):
                    # spell cast not interrupted, therefore not cancelled.
                    continue

                if source in casting_dict:
                    cast = casting_dict.pop(source)
                    (start_time, _, _) = cast
                else:
                    start_time = cancel_time

                cast = (source, start_time, cancel_time, spell_id, f"[{reason}]")
                cast_list.append(cast)

            elif "SPELL_HEAL" in line_parts[0]:
                heal_time = get_time_stamp(line_parts[0])
                source = get_player_name(line_parts[2])
                target = get_player_name(line_parts[6])
                spell_id = line_parts[9]

                # align with batch window
                if not batch_time or heal_time > batch_time:
                    batch_time = heal_time
                    batch_i = 0

                heal_amount = int(line_parts[29])  # total heal
                overheal_amount = int(line_parts[30])  # total heal
                net_heal = heal_amount - overheal_amount
                heals.append((source, heal_time, batch_i, spell_id, target, net_heal))

                batch_i += 1

        full_heal_data = []

        # match up casts and heals
        for source, heal_time, batch_i, spell_id, target, net_heal in heals:
            if source not in casts:
                continue

            for c in casts[source]:
                start_time = c[1]
                success_time = c[2]
                c_id = c[3]
                # c_target = c[4]

                if (
                    c_id == spell_id
                    # and c_target == target
                    and success_time <= heal_time + timedelta(seconds=0.1)
                ):
                    # found a match
                    full_heal = (source, start_time, success_time, heal_time, batch_i, spell_id, target, net_heal)
                    full_heal_data.append(full_heal)

                    casts[source].remove(c)

        return cast_list, full_heal_data


def get_heals(source, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(source, normalise_time=normalise_time, character_name=character_name)
    line_processor.process()

    return line_processor.heals, line_processor.periodic_heals


def get_heals_and_damage(source, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(
        source, normalise_time=normalise_time, character_name=character_name, include_damage=True
    )
    line_processor.process()

    return line_processor.all_events


def get_processed_lines(source, character_name=None, normalise_time=True, **_):
    line_processor = RawProcessor(
        source, normalise_time=normalise_time, character_name=character_name, include_damage=True
    )
    line_processor.process()

    return line_processor
