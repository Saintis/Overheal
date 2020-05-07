"""
Script that gets the probability of an overheal based of +heal.

By: Filip Gokstorp (Saintis), 2020
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap

import overheal_table as ot
import process_raw_logs as raw
import spell_data as sd


def spell_overheal_probability(player_name, spell_id, lines, spell_power=None):
    """Plots overheal probability of each spell"""

    if spell_power is None:
        sp_neg = 400.0
        sp_shift = 0.0
        sp_extrap = 200.0
    else:
        sp_neg = spell_power
        sp_shift = spell_power
        sp_extrap = 1000.0 - spell_power

        if sp_extrap < 0:
            sp_extrap = 1500.0 - spell_power

    spell_powers = np.linspace(0, -sp_neg, int(sp_neg / 1) + 1)
    oh_probabilities = []
    oh_p_no_crit = []

    # Fail more gracefully if we are missing a coefficient
    coefficient = sd.spell_coefficient(spell_id)
    if coefficient == 0:
        return

    n_samples = np.inf
    n_samples_no_crit = np.inf

    for sp in spell_powers:
        n_heals = 0
        n_overheals = 0
        n_heals_no_crit = 0
        n_oh_no_crit = 0

        for h, oh, crit in lines:
            dh = coefficient * -sp

            if crit:
                # scale spell power differential by 1.5 if spell was a crit
                dh *= 1.5

            h = h - dh
            oh = oh - dh

            if h < 0.0:
                # could happen for heals on healing reduced players, we just ignore these for now
                continue

            n_heals += 1

            if oh > 0.0:
                n_overheals += 1

            if not crit:
                n_heals_no_crit += 1

                if oh > 0.0:
                    n_oh_no_crit += 1

        n_samples = min(n_heals, n_samples)
        n_samples_no_crit = min(n_heals_no_crit, n_samples_no_crit)

        oh_probabilities.append(n_overheals / n_heals)
        oh_p_no_crit.append(n_oh_no_crit / n_heals_no_crit)

    # extrapolate from first 1/2 of data (0 - spell_power / 2)
    ii = len(spell_powers) // 2
    e_sp = np.linspace(spell_powers[ii], sp_extrap, 101)

    plt.figure(constrained_layout=True)

    p = np.polyfit(spell_powers[:ii], oh_probabilities[:ii], 1)
    plt.plot(e_sp + sp_shift, np.polyval(p, e_sp), "b--", label="Extrapolation")
    plt.plot(spell_powers + sp_shift, oh_probabilities, label=f"All heals (N={n_samples})")

    p = np.polyfit(spell_powers[:ii], oh_p_no_crit[:ii], 1)
    plt.plot(e_sp + sp_shift, np.polyval(p, e_sp), "r--", label="Extrapolation, no crits")
    plt.plot(spell_powers + sp_shift, oh_p_no_crit, label=f"No crits (N={n_samples_no_crit})")

    plt.title(f"Overheal probability of {sd.spell_name(spell_id)}")
    plt.ylabel("Overheal probability")
    plt.ylim([0, 1])
    plt.xlabel("Heal power change")
    plt.yticks([0, 0.25, 0.5, 0.75, 1.0])

    plt.grid()
    plt.legend()

    plt.savefig(f"figs/{player_name}_overheal_probability_{spell_id}.png")
    # plt.show()


def process_log(player_name, log_file, spell_power=500, ignore_crit=False, spell_id=None, **kwargs):
    log_lines = raw.get_lines(log_file)
    heal_lines, _ = raw.get_heals(player_name, log_lines)

    os.makedirs("figs", exist_ok=True)

    # Group lines
    _, heal_lines = ot.group_processed_lines(heal_lines, ignore_crit, spell_id=spell_id)
    for spell_id, lines in heal_lines.items():
        spell_overheal_probability(player_name, spell_id, lines, spell_power)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Plots probability of overheals for different spells.""",
    )

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument("--ignore_crit", action="store_true", help="Remove critical heals from analysis")
    parser.add_argument("--spell_id", type = str, help = "Spell id to print figure for. If None, prints for all found spells")
    parser.add_argument("-p", "--spell_power", type=int, help="Character spell power. If None, only look at spell power change relative to current amount", default=None)

    args = parser.parse_args()

    process_log(args.player_name, args.log_file, spell_power=args.spell_power, ignore_crit=args.ignore_crit, spell_id=args.spell_id)
