"""
Optimise spell casts to heal damage taken.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from collections import namedtuple

from backend import encounter_picker
from readers import read_from_raw as raw
from damage.track_damage import track_raid_damage


CharacterData = namedtuple("CharacterData", ("h", "a", "mp5", "mp5ooc", "mana"))


def optimise_casts(times, deficits, character_data):
    pass


def main(argv=None):
    from backend.parser import OverhealParser

    parser = OverhealParser(need_character=True, accept_encounter=True)
    args = parser.parse_args(argv)

    lines = raw.get_lines(args.source)

    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(lines, args.encounter)
    data = raw.get_processed_lines(encounter_lines, ref_time=encounter_start)
    events = data.all_events

    # encounter_time = (encounter_end - encounter_start).total_seconds()
    character_data = CharacterData(800, 0.25, 32, 200, 8000)

    times, deficits, _ = track_raid_damage(
        events, character_name=args.character_name, verbose=args.verbose
    )

    optimise_casts(times, deficits, character_data)


if __name__ == "__main__":
    main()
