"""
Evaluate cast time saved / could have been saved by using 3 T1.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""

from datetime import datetime

import read_from_raw as raw

ENCOUNTER_START = "ENCOUNTER_START"
ENCOUNTER_END = "ENCOUNTER_END"

STR_P_TIME = "%m/%d %H:%M:%S.%f"


def get_flash_heal_casts(character_name, log_lines):
    """Get spell casts and time stamps for specified character in lines."""

    flash_casts = 0
    t1_3_uses = 0
    t1_3_potentials = 0

    t_start = None
    t_end = None

    for line in log_lines:
        line_parts = line.split(",")

        if "SPELL_CAST_START" in line_parts[0] and line_parts[10] == '"Flash Heal"':
            # Starting to cast flash heal
            source = line_parts[2].split("-")[0][1:]

            if character_name != source:
                continue

            t_start = datetime.strptime(line_parts[0].split("  ")[0], STR_P_TIME)

            if t_end is None:
                continue

            # compare delay since last cast
            d_cast = (t_start - t_end).total_seconds()
            if d_cast < 0.1:
                t1_3_uses += 1

        elif "SPELL_CAST_SUCCESS" in line_parts[0] and line_parts[10] == '"Flash Heal"':
            source = line_parts[2].split("-")[0][1:]

            if character_name != source:
                continue

            flash_casts += 1

            if t_start is None:
                continue

            t_end = datetime.strptime(line_parts[0].split("  ")[0], STR_P_TIME)

    return flash_casts, t1_3_uses


def main(args):
    character_name = args.character_name

    lines = raw.get_lines(args.log_file)
    fh_casts, t1_3_uses = get_flash_heal_casts(character_name, lines)

    print("Evaluation of 3T1:")
    print(f"  Used Flash Heal {fh_casts} times.")
    print(f"  Found {t1_3_uses} back-to-back casts (within 0.1s).")
    print(f"  3T1 is worth {t1_3_uses * 0.1:.1f}s of casting.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate 3 piece T1 set. Counts number of times flash heal casts were back-to-back with less than"
                    " 0.1s between.",
    )

    parser.add_argument("character_name")
    parser.add_argument("log_file", help="Path to the log file to analyse")

    args = parser.parse_args()

    main(args)

