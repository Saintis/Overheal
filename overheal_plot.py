"""
Script that generates plot of the overheals.

By: Filip Gokstorp (Saintis), 2020
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap

import overheal_table as ot
import process_raw_logs as raw


def process_log(player_name, log_file, ignore_crit=False, spell_id=None, **kwargs):
    heal_lines, periodic_lines = raw.get_lines(player_name, log_file)

    os.makedirs("figs", exist_ok=True)

    # Group lines
    names, heal_lines = ot.group_processed_lines(heal_lines, ignore_crit, spell_id=spell_id)

    spell_powers = np.arange(0, 500 + 1, 5)
    total_heals = []
    total_overheals = []
    total_actual_heals = []

    for sp in spell_powers:
        total_data, _ = ot.aggregate_lines(heal_lines, spell_power=sp)

        n_heals = total_data[0]
        heal = total_data[4]
        overheal = total_data[5]
        actual_heal = total_data[4] - total_data[5]

        total_heals.append(heal / n_heals)
        total_overheals.append(overheal / n_heals)
        total_actual_heals.append(actual_heal / n_heals)

    plt.figure()
    plt.plot(spell_powers, total_heals, label="Total healing")
    plt.plot(spell_powers, total_overheals, label="Total overheal")
    plt.plot(spell_powers, total_actual_heals, label="Total actual heal")

    plt.title("\n".join(wrap("Average healing per cast as you artifically remove spell power.", 60)))
    plt.xlabel("Removed heal power")
    plt.ylabel("Healing")
    plt.ylim([0, None])

    plt.grid()
    plt.legend()
    plt.tight_layout()

    plt.savefig("figs/total_heal.png")

    # gradient figure
    d_sp = np.diff(spell_powers)
    sp = 0.5 * (spell_powers[1:] + spell_powers[:-1])

    plt.figure()
    plt.plot(sp, np.diff(total_heals) / d_sp, label="Total healing")
    plt.plot(sp, np.diff(total_overheals) / d_sp, label="Total overhealing")
    plt.plot(sp, np.diff(total_actual_heals) / d_sp, label="Total actual heal")

    plt.title("\n".join(wrap("Average healing per spell power lost as you artifically remove spell power.", 70)))
    plt.xlabel("Removed heal power")
    plt.ylabel("d(Healing)/d(Spell power)")
    # plt.ylim([0, None])

    plt.grid()
    plt.legend()
    plt.tight_layout()

    # flipped figure
    sp = max(spell_powers) - spell_powers
    d_sp = np.diff(sp)
    sp = 0.5 * (sp[1:] + sp[:-1])

    dh = np.diff(total_actual_heals) / d_sp

    plt.figure()
    plt.plot(sp, np.diff(total_heals) / d_sp, label="Total healing")
    plt.plot(sp, np.diff(total_overheals) / d_sp, label="Total overhealing")
    plt.plot(sp, dh, label="Total actual heal")

    # linear fit of coefficient
    coef = np.polyfit(sp, dh, 1)
    plt.plot(sp, np.poly1d(coef)(sp), "k--", label=f"Linear fit, Sc={coef[0] * 100:.2g} * 100h + {coef[1]:.2g}")

    plt.title("\n".join(wrap("Starting from already reduced spell power, average healing per spell power gained as you recover spell power. This is the plot you could maybe extrapolate to infer value of additional spell power. Note that the blue line is the average spell coefficient of the casting profile.", 70)))
    plt.xlabel("Recovered heal power")
    plt.ylabel("d(Healing)/d(Spell power)")
    plt.ylim([0, None])

    plt.grid()
    plt.legend()
    plt.tight_layout()

    plt.savefig("figs/adj_spell_coef.png")

    plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Analyses logs and count up number of overheals. Returns a list of spells and the number of recorded heals, as well as overheal frequencies.

Header explaination:
    #H: Number of heals recorded.
    No OH: Percentage of heals that had no overheal (underheals).
    Any OH: Percantage of heals that had 1 or more overheal.
    Half OH: Percentage of heals that overhealed for at least 50% of the heal value.
    Full OH: Percentage of heals that overhealed for at least 90% of the heal value.
    % OHd: Percentage of heal values that were overheal, same overheal percentage shown in WarcraftLogs. """,
    )

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument("--ignore_crit", action="store_true", help="Remove critical heals from analysis")
    parser.add_argument("--spell_id", type=str, help="Spell id to filter for")

    args = parser.parse_args()

    process_log(args.player_name, args.log_file, ignore_crit=args.ignore_crit, spell_id=args.spell_id)
