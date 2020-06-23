"""
Python script that estimates spell power from logs.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np

from readers import read_heals
from backend import group_processed_lines

import spell_data as sd


def filter_out_reduced_healing(raw_heals):
    """Reduced healing will be max 75% of highest recorded heal. Just remove all heals below 75% of max heal."""
    max_heal = max(raw_heals)
    threshold = 0.75 * max_heal

    selector = raw_heals > threshold

    return raw_heals[selector]


def process_spell(spell_id, spell_lines, heal_increase=0.0):
    spell_name = sd.spell_name(spell_id)

    n_heals = 0
    n_crits = 0
    raw_heals = []

    for h, _, crit in spell_lines:
        n_heals += 1

        if crit:
            n_crits += 1
            h /= 1.5

        raw_heals.append(h)

    raw_heals = np.array(raw_heals)

    raw_heals = filter_out_reduced_healing(raw_heals)
    sample_size = len(raw_heals)

    median_heal = np.median(raw_heals)
    crit_rate = n_crits / n_heals

    # Include heal increase from Improved Renew or Spiritual Healing
    spell_heal = sd.spell_heal(spell_id)
    spell_heal *= (1.0 + heal_increase)

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

    print(
        f"  {spell_id:>5s}  {spell_name:>26s}  {sample_size:3d}  {spell_heal:+7.1f}  {median_heal:+7.1f}"
        f"  {extra_heal:+6.1f}  {est_plus_heal:+7.1f}  {crit_rate:5.1%}"
    )

    return est_plus_heal, n_heals, n_crits


def estimate_spell_power(source, character_name, spell_id=None, spiritual_healing=0, improved_renew=0, **kwargs):
    heal_lines, periodic_lines, _ = read_heals(source, character_name=character_name, spell_id=spell_id, **kwargs)

    if spiritual_healing > 5:
        spiritual_healing = 5

    if improved_renew > 3:
        improved_renew = 3

    # Group lines
    heal_lines = group_processed_lines(heal_lines, False, spell_id=spell_id)
    periodic_lines = group_processed_lines(periodic_lines, False, spell_id=spell_id)

    print()

    print(f"  Spiritual Healing:  {spiritual_healing:d} / 5")
    print(f"  Improved Renew:     {improved_renew:d} / 3")

    print()
    print(
        f"  {'id':>5s}  {'name':>26s}  {'#':>3s}  {'base H':>7s}  {'mean H':>7s}  {'extr H':>6s}  {'Est.+H':>7s}"
        f"  {'Crit':>5s}"
    )
    print()

    if spell_id:
        # only one will be populated
        lines = heal_lines + periodic_lines
        process_spell(spell_id, lines[spell_id])
    else:
        spell_inc = 0.02 * spiritual_healing

        nn_heals = 0
        nn_crits = 0
        estimates = []

        for spell_id, lines in heal_lines.items():
            est_plus_heal, n_heals, n_crits = process_spell(spell_id, lines, heal_increase=spell_inc)
            nn_heals += n_heals
            nn_crits += n_crits
            estimates.append(est_plus_heal)

        print()

        renew_inc = 0.05 * improved_renew
        for spell_id, lines in periodic_lines.items():
            if spell_id == "22009":
                # 8t2 does not benefit from talent healing increases
                process_spell(spell_id, lines, heal_increase=0)
            else:
                process_spell(spell_id, lines, heal_increase=spell_inc + renew_inc)

        print()

        print(f"  Estimated Spell crit: {nn_crits / nn_heals:.1%}")

    print()


if __name__ == "__main__":
    from backend.parser import OverhealParser

    parser = OverhealParser(
        description="Analyses logs and and estimates spell power and crit chance.",
        need_character=True,
        accept_spell_id=True,
    )

    parser.add_argument("--sh", type=int, help="Levels of Spirital Healing to guess", default=0)
    parser.add_argument("--ir", type=int, help="Levels of Improved Renew to guess", default=0)

    args = parser.parse_args()

    estimate_spell_power(args.source, args.character_name, args.spell_id, args.sh, args.ir)
