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
from spell_data import SPELL_NAMES


def process_log(player_name, log_file, spell_power=500, ignore_crit=False, spell_id=None, **kwargs):
    log_lines = raw.get_lines(log_file)
    heal_lines, periodic_lines = raw.get_heals(player_name, log_lines)

    os.makedirs("figs", exist_ok=True)

    # Group lines
    names, heal_lines = ot.group_processed_lines(heal_lines, ignore_crit, spell_id=spell_id)

    spell_powers = np.linspace(0, spell_power, 101)
    sp = max(spell_powers) - spell_powers
    total_heals = []
    total_overheals = []
    total_actual_heals = []

    nn_underheals = []
    nn_overheals = []
    nn_half_overheals = []
    nn_full_overheals = []

    for s in spell_powers:
        total_data, _ = ot.aggregate_lines(heal_lines, spell_power=s)

        n_heals = total_data[0]
        n_overheals = total_data[1]
        n_half_overheals = total_data[2]
        n_full_overheals = total_data[3]

        heal = total_data[4]
        overheal = total_data[5]
        actual_heal = total_data[4] - total_data[5]

        # print(f"sp: {s}  N: {n_heals}  O: {n_overheals}  H: {heal:.0f}  OH: {overheal:.0f}")

        total_heals.append(heal / n_heals)
        total_overheals.append(overheal / n_heals)
        total_actual_heals.append(actual_heal / n_heals)

        nn_underheals.append((n_heals - n_overheals) / n_heals)
        nn_overheals.append(n_overheals / n_heals)
        nn_half_overheals.append(n_half_overheals / n_heals)
        nn_full_overheals.append(n_full_overheals / n_heals)

    plt.figure()
    plt.plot(sp, total_heals, label="Total heal")
    plt.plot(sp, total_overheals, label="Overheal")
    plt.plot(sp, total_actual_heals, label="Actual heal")

    plt.title("\n".join(wrap("Average healing per cast as +heal varies", 60)))
    plt.xlabel("Heal power")
    plt.ylabel("Healing output")
    plt.ylim([0, None])

    plt.grid()
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"figs/{player_name}_total_heal.png")

    # number of heals figure
    fig = plt.figure(figsize=(10, 4), constrained_layout=True)
    ax1, ax2 = fig.subplots(1, 2)

    ax1.plot(sp, nn_underheals, label="Underheal")
    ax1.plot(sp, nn_overheals, label="Any overheal")
    ax1.plot(sp, nn_half_overheals, label="Half overheal")
    ax1.plot(sp, nn_full_overheals, label="Full overheal")

    title = "Number of overheals as a +heal varies"
    if spell_id:
        title = SPELL_NAMES[spell_id] + "\n" + title

    ax1.set_title(title)
    ax1.set_xlabel("Heal power")
    ax1.set_ylabel("Overheal fraction of total casts")
    ax1.set_ylim([0.0, 1.0])

    ax1.grid()
    ax1.legend()

    # gradient figure
    d_sp = np.diff(sp)
    sp = 0.5 * (sp[1:] + sp[:-1])

    dh = np.diff(total_actual_heals) / d_sp

    ax2.plot(sp, np.diff(total_heals) / d_sp, label="Total heal")
    ax2.plot(sp, np.diff(total_overheals) / d_sp, label="Overheal")
    ax2.plot(sp, dh, label="Actual heal")

    # linear fit of coefficient
    # coef = np.polyfit(sp, dh, 1)
    # ax2.plot(sp, np.poly1d(coef)(sp), "k--", label=f"Linear fit, Sc={coef[0] * 100:.2g} * 100h + {coef[1]:.2g}")

    # plt.title("\n".join(wrap("Starting from already reduced spell power, average healing per spell power gained as you recover spell power. This is the plot you could maybe extrapolate to infer value of additional spell power. Note that the blue line is the average spell coefficient of the casting profile.", 70)))

    title = "Effective spell coefficient as total +heal varies"
    if spell_id:
        title = SPELL_NAMES[spell_id] + "\n" + title

    ax2.set_title(title)
    ax2.set_xlabel("Heal power")
    ax2.set_ylabel("d(Healing)/d(Spell power)")
    ax2.set_ylim([0.0, 1.0])

    ax2.grid()
    ax2.legend()

    fig_name = f"{player_name}_overheal"
    if spell_id:
        fig_name += "_" + spell_id

    plt.savefig(f"figs/{fig_name}.png")

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
    parser.add_argument("--spell_id", type = str, help = "Spell id to filter for")
    parser.add_argument("-p", "--spell_power", type=int, help="Spell power range to look at", default=500)

    args = parser.parse_args()

    process_log(args.player_name, args.log_file, args.spell_power, ignore_crit=args.ignore_crit, spell_id=args.spell_id)
