"""
Python script that estimates spell power from logs.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np
import matplotlib.pyplot as plt

import process_raw_logs as raw
import spell_data as sd
from overheal_table import group_processed_lines


def filter_out_reduced_healing(raw_heals, is_crit):
    """Reduced healing will be max 75% of highest recorded heal. Just remove all heals below 75% of max heal."""
    max_heal = max(raw_heals)
    threshold = 0.75 * max_heal

    selector = (raw_heals > threshold)

    return raw_heals[selector], is_crit[selector]


def process_spell(spell_id, spell_lines, heal_increase=0.0):
    spell_name = sd.spell_name(spell_id)

    raw_heals = []
    is_crit = []

    for h, _, crit in spell_lines:
        c = 0
        if crit:
            c = 1
            h /= 1.5

        raw_heals.append(h)
        is_crit.append(c)

    raw_heals = np.array(raw_heals)
    is_crit = np.array(is_crit)

    raw_heals, is_crit = filter_out_reduced_healing(raw_heals, is_crit)

    sample_size = len(raw_heals)

    median_heal = np.median(raw_heals)
    crit_rate = np.mean(is_crit)

    # Include heal increase from Improved Renew or Spiritual Healing
    spell_heal = sd.spell_heal(spell_id) * (1 + heal_increase)

    if spell_heal == 0:
        # Unknown or 0 base heal, cannot estimate +heal
        extra_heal = 0.0
    else:
        extra_heal = median_heal - spell_heal

    coefficient = sd.spell_coefficient(spell_id)
    if coefficient == 0:
        # Unknown or 0 coefficient, cannot estimate +heal
        est_plus_heal = 0
    else:
        est_plus_heal = extra_heal / coefficient

    print(f"  {spell_id:>5s}  {spell_name:>26s}  {sample_size:3d}  {spell_heal:+5.0f}  {median_heal:+5.0f}  {extra_heal:+5.0f}  {est_plus_heal:+5.0f}  {crit_rate:5.1%}")

    return est_plus_heal, crit_rate


def estimate_spell_power(player_name, log_file, spell_id=None, spiritual_healing=0, improved_renew=0, **kwargs):
    heal_lines, periodic_lines = raw.get_lines(player_name, log_file)

    # Group lines
    _, heal_lines = group_processed_lines(heal_lines, False, spell_id=spell_id)
    _, periodic_lines = group_processed_lines(periodic_lines, False, spell_id=spell_id)

    print(f"  {'id':>5s}  {'name':>26s}  {'#':>3s}  {'bHeal':>5s}  {'mHeal':>5s}  {'eHeal':>5s}  {'Est+H':>5s}  {'Crit':>5s}")

    if spell_id:
        # only one will be populated
        lines = heal_lines + periodic_lines
        process_spell(spell_id, lines[spell_id])
        # process_spell(spell_id, periodic_lines[spell_id])
    else:
        for spell_id, lines in heal_lines.items():
            process_spell(spell_id, lines, heal_increase=0.02 * spiritual_healing)

        for spell_id, lines in periodic_lines.items():
            process_spell(spell_id, lines, heal_increase=0.05 * improved_renew)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Analyses logs and and estimates spell power and crit chance.
"""
)

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument("--spell_id", type=str, help="Spell id to filter for")
    parser.add_argument("--sh", type=int, help="Levels of Spirital Healing to guess")
    parser.add_argument("--ir", type=int, help="Levels of Improved Renew to guess")

    args = parser.parse_args()

    estimate_spell_power(args.player_name, args.log_file, args.spell_id, spiritual_healing=args.sh, improved_renew=args.ir)
