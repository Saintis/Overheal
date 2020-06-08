"""
Evaluate cast time saved / could have been saved by using 3T1 bonus.

Whenever a spell is cast, check if the previous spell as a FH and new spell was cast within 0.1s of the FH. That cast
 would (likely) have benefited from 3T1 bonus.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""

from readers import read_from_raw as raw
from backend import encounter_picker, get_player_name, get_time_stamp


def get_flash_heal_casts(character_name, log_lines):
    """Get spell casts and time stamps for specified character in lines."""

    flash_casts = 0
    t1_3_potentials = 0

    t_end = None

    for line in log_lines:
        line_parts = line.split(",")

        if "SPELL_CAST_SUCCESS" in line_parts[0] and line_parts[10] == '"Flash Heal"':
            # Finished casting Flash Heal
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            flash_casts += 1

            t_end = get_time_stamp(line_parts[0])

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
    lines = raw.get_lines(source)
    encounter, encounter_lines, e_start, e_end = encounter_picker(lines, encounter_i=encounter_i)
    e_time = (e_end - e_start).total_seconds()
    fh_casts, t1_3_uses = get_flash_heal_casts(character_name, encounter_lines)

    if encounter is None:
        encounter = "All encounters"

    print(f"Evaluation of 3T1  ({encounter}, {e_time:.0f}s)")
    print(f"  Used Flash Heal {fh_casts} times.")
    print(f"  Found {t1_3_uses} back-to-back casts (within 0.1s).")
    print(f"  3T1 is worth {t1_3_uses * 0.1:.1f}s of casting.")


def main(argv=None):
    from backend.parser import OverhealParser

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

