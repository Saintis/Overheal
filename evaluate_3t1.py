"""
Evaluate cast time saved / could have been saved by using 3T1 bonus.

Whenever a spell is cast, check if the previous spell as a FH and new spell was cast within 0.1s of the FH. That cast
 would (likely) have benefited from 3T1 bonus.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""

from src.readers import read_from_raw as raw
from src.utils import get_player_name, get_time_stamp
from src.readers import get_processor


def get_flash_heal_casts(character_name, log_lines):
    """Get spell casts and time stamps for specified character in lines."""

    flash_casts = 0
    t1_3_potentials = 0

    t_end = None

    for line in log_lines:
        line_parts = line.split(",")

        if "SPELL_CAST_SUCCESS" in line_parts[0]:
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            if line_parts[10] == '"Flash Heal"':
                # Finished casting Flash Heal
                flash_casts += 1

                t_end = get_time_stamp(line_parts[0])
            else:
                # Could have cast an instant spell
                t_start = get_time_stamp(line_parts[0])

                if t_end is None:
                    continue

                # compare delay since last cast
                d_cast = (t_start - t_end).total_seconds()
                if d_cast < 0.1:
                    t1_3_potentials += 1

        elif "SPELL_CAST_START" in line_parts[0]:
            # Starting to cast a spell
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            t_start = get_time_stamp(line_parts[0])

            if t_end is None:
                continue

            # compare delay since last cast
            d_cast = (t_start - t_end).total_seconds()
            if d_cast < 0.1:
                t1_3_potentials += 1

    return flash_casts, t1_3_potentials


def evaluate_3t1(source, character_name, encounter_i=None):
    """Evaluate number of Flash Heals back-to-back."""
    if "http://" in source or "https://" is source:
        print("Evaluate 3T1 only works with a combatlog txt file, it does not work with a WCL link yet.")
        return

    processor = get_processor(source, character_name=character_name)
    encounter = processor.select_encounter(encounter_i)

    lines = raw.get_lines(source)
    e_time = encounter.duration
    encounter_lines = lines[encounter.start : encounter.end]
    fh_casts, t1_3_potentials = get_flash_heal_casts(character_name, encounter_lines)

    fh_ratio = 0 if fh_casts == 0 else t1_3_potentials / fh_casts

    print(f"Evaluation of 3T1  ({encounter.boss}, {e_time:.0f}s)")
    print(f"  Used Flash Heal {fh_casts} times.")
    print(f"  Found {t1_3_potentials} back-to-back casts after a Flash Heal (within 0.1s) ({fh_ratio:.1%}).")
    print(
        f"  3T1 is potentially worth {t1_3_potentials * 0.1:.1f}s of casting"
        f" ({t1_3_potentials / 14:.0f} more Flash Heals)."
    )


def main(argv=None):
    from src.parser import OverhealParser

    parser = OverhealParser(
        description="Evaluate 3 piece T1 set. Counts number of times flash heal casts were back-to-back with less than"
        " 0.1s between.",
        need_character=True,
        accept_encounter=True,
    )
    args = parser.parse_args(argv)

    evaluate_3t1(args.source, args.character_name, encounter_i=args.encounter)


if __name__ == "__main__":
    main()
