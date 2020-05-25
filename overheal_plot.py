"""
Script that generates plot of the overheals.

By: Filip Gokstorp (Saintis), 2020
"""
import os

import numpy as np
import matplotlib.pyplot as plt

from readers import read_heals
from backend import group_processed_lines

import spell_data as sd


def plot_overheal(player_name, spell_powers, spell_id, data, sp_shift=0, sp_extrap=200):
    os.makedirs("figs/overheal", exist_ok=True)

    sp = spell_powers + sp_shift
    spell_name = sd.spell_name(spell_id)

    total_heals, total_overheals, total_underheals, count_heals, nn_underheals, nn_overheals, nn_full_overheals = data

    plt.figure()
    plt.plot(sp, total_heals, label="Total heal")
    plt.plot(sp, total_overheals, label="Overheal")
    plt.plot(sp, total_underheals, label="Actual heal")

    plt.title(f"Average healing per cast as +heal varies\n{spell_name}")
    plt.xlabel("Heal power")
    plt.ylabel("Healing output")
    plt.ylim([0, None])

    plt.grid()
    plt.legend()
    plt.tight_layout()

    fig_name = f"{player_name}_heal"
    if spell_id:
        fig_name += "_" + spell_id

    plt.savefig(f"figs/overheal/{fig_name}.png")

    # number of heals figure
    fig = plt.figure(figsize=(10, 4), constrained_layout=True)
    ax1, ax2 = fig.subplots(1, 2)

    ax1.plot(sp, nn_underheals, label="Underheal")
    ax1.plot(sp, nn_overheals, label="Any overheal")
    ax1.plot(sp, nn_full_overheals, label="Full overheal")

    title = "Number of overheals as a +heal varies"
    if spell_id:
        title = sd.spell_name(spell_id) + "\n" + title

    ax1.set_title(title)
    ax1.set_xlabel("Heal power")
    ax1.set_ylabel("Overheal fraction of total casts")
    ax1.set_ylim([0.0, 1.0])

    ax1.grid()
    ax1.legend()

    # gradient figure
    d_sp = np.diff(spell_powers)
    sp = 0.5 * (sp[1:] + sp[:-1])

    dth = np.diff(total_heals) / d_sp
    doh = np.diff(total_overheals) / d_sp
    dh = np.diff(total_underheals) / d_sp

    ax2.plot(sp, dth, label="Total heal")
    ax2.plot(sp, doh, label="Overheal")
    ax2.plot(sp, dh, label="Net heal")

    # linear fit of coefficient
    # coef = np.polyfit(sp, dh, 1)
    # ax2.plot(sp, np.poly1d(coef)(sp), "k--", label=f"Linear fit, Sc={coef[0] * 100:.2g} * 100h + {coef[1]:.2g}")

    title = "Effective spell coefficient as total +heal varies"
    if spell_id:
        title = sd.spell_name(spell_id) + "\n" + title

    ax2.set_title(title)
    ax2.set_xlabel("Heal power")
    ax2.set_ylabel("d(Healing)/d(Spell power)")
    ax2.set_ylim([0.0, 1.0])

    ax2.grid()
    ax2.legend()

    fig_name = f"{player_name}_overheal"
    if spell_id:
        fig_name += "_" + spell_id

    plt.savefig(f"figs/overheal/{fig_name}.png")


def process_lines_for_spell(lines, dh, base_heal=None):
    """
    Counts up heals and overheals, as well as sum heal and overheal amounts for given spell power adjustment.
    """
    n_h = 0
    n_oh = 0
    n_f_oh = 0
    n_oh_nc = 0

    total_h = 0.0
    total_oh = 0.0

    total_h_nc = 0.0
    total_oh_nc = 0.0

    for h, oh, crit in lines:
        dh_c = dh

        oh_nc = oh
        h_nc = h

        if base_heal and h < base_heal:
            # Skip unexpectedly low heals
            continue

        if crit:
            # scale spell power differential by 1.5 if spell was a crit
            dh_c *= 1.5

            # Scale oh down
            h_nc = h / 1.5
            oh_nc = oh - (h - h_nc)

        # remove spell power contribution
        h -= dh_c
        oh -= dh_c
        if oh < 0.0:
            oh = 0.0

        h_nc -= dh
        oh_nc -= dh
        if oh_nc < 0.0:
            oh_nc = 0.0

        n_h += 1

        if oh > 0.0:
            n_oh += 1
            if oh >= h:
                n_f_oh += 1

        if oh_nc > 0.0:
            n_oh_nc += 1

        total_h += h
        total_oh += oh

        total_h_nc += h_nc
        total_oh_nc += oh_nc

    return n_h, n_oh, n_f_oh, n_oh_nc, total_h, total_oh, total_h_nc, total_oh_nc


def group_lines_for_spell(spell_id, lines, spell_powers):
    total_heals = []
    total_overheals = []
    total_underheals = []

    count_heals = []

    nn_underheals = []
    nn_overheals = []
    nn_full_overheals = []

    coefficient = sd.spell_coefficient(spell_id)
    base_heal = sd.spell_heal(spell_id)

    for i, sp in enumerate(spell_powers):
        data = process_lines_for_spell(lines, -sp * coefficient, base_heal)
        n_h, n_oh, n_f_oh, n_oh_nc, total_h, total_oh, total_h_nc, total_oh_nc = data

        total_heals.append(total_h / n_h)
        total_overheals.append(total_oh / n_h)
        total_underheals.append((total_h - total_oh) / n_h)

        count_heals.append(n_h)

        nn_underheals.append((n_h - n_oh) / n_h)
        nn_overheals.append(n_oh / n_h)
        nn_full_overheals.append(n_f_oh / n_h)

    return total_heals, total_overheals, total_underheals, count_heals, nn_underheals, nn_overheals, nn_full_overheals


def main(
    player_name, source, ignore_crit=False, spell_id=None, spell_power=None, **kwargs
):
    heal_lines, periodic_lines, absorbs = read_heals(player_name, source, spell_id=spell_id, **kwargs)

    # Group lines
    heal_lines = group_processed_lines(
        heal_lines, ignore_crit, spell_id=spell_id
    )

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

    for spell_id, lines in heal_lines.items():
        out = group_lines_for_spell(spell_id, lines, spell_powers)
        plot_overheal(player_name, spell_powers, spell_id, out, sp_shift=sp_shift, sp_extrap=sp_extrap)


if __name__ == "__main__":
    import argparse
    from backend.parser import OverhealParser

    parser = OverhealParser(
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
        need_player=True,
        accept_spell_id=True,
        accept_spell_power=True
    )

    parser.add_argument(
        "--ignore_crit", action="store_true", help="Remove critical heals from analysis"
    )

    args = parser.parse_args()

    main(**vars(args))
