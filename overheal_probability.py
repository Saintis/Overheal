"""
Script that gets the probability of an overheal based of +heal.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np
import matplotlib.pyplot as plt

from readers import read_heals
from backend import group_processed_lines

import spell_data as sd


def plot_oh_prob(
    player_name,
    spell_id,
    spell_powers,
    sp_extrap,
    sp_shift,
    n_heals,
    n_overheals,
    n_overheals_nc,
):
    # extrapolate from first 1/2 of data (0 - spell_power / 2)
    ii = len(spell_powers) // 2
    e_sp = np.linspace(spell_powers[ii], sp_extrap, 101)

    oh_p = np.divide(n_overheals, n_heals)
    oh_p_nc = np.divide(n_overheals_nc, n_heals)

    ns = min(n_heals)
    # ns_nc = min(n_heals_nc)

    plt.figure(constrained_layout=True)

    p = np.polyfit(spell_powers[:ii], oh_p[:ii], 1)
    plt.plot(e_sp + sp_shift, np.polyval(p, e_sp), "b--", label="Extrapolation")
    plt.plot(spell_powers + sp_shift, oh_p, label=f"All heals")

    p = np.polyfit(spell_powers[:ii], oh_p_nc[:ii], 1)
    plt.plot(
        e_sp + sp_shift, np.polyval(p, e_sp), "r--", label="Extrapolation, no crits"
    )
    plt.plot(spell_powers + sp_shift, oh_p_nc, label=f"No crits")

    plt.title(f"Overheal probability of {sd.spell_name(spell_id)}, (N={ns})")
    plt.ylabel("Overheal probability")
    plt.ylim([0, 1])
    plt.xlabel("Heal power change")
    plt.yticks([0, 0.25, 0.5, 0.75, 1.0])

    plt.grid()
    plt.legend()

    plt.savefig(f"figs/probability/{player_name}_probability_{spell_id}.png")

    # Likelihood plot
    plt.figure(constrained_layout=True)

    p_oh = np.linspace(0, 1, 1001)
    l_oh = p_oh ** n_overheals[0] * (1.0 - p_oh) ** (n_heals[0] - n_overheals[0])
    plt.plot(p_oh, l_oh)

    plt.title(f"Overheal probability likelihood of {sd.spell_name(spell_id)} (N={n_heals[0]})")
    plt.ylabel("Overheal probability likelihood")
    # plt.ylim([0, 1])
    plt.xlabel("Overheal probability")
    # plt.yticks([0, 0.25, 0.5, 0.75, 1.0])

    plt.grid()
    # plt.legend()

    plt.savefig(f"figs/probability/likelihood/{player_name}_likelihood_{spell_id}.png")


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
    n_heals = []
    n_overheals = []
    n_overheals_nc = []

    # Fail more gracefully if we are missing a coefficient
    coefficient = sd.spell_coefficient(spell_id)
    if coefficient == 0:
        return

    for sp in spell_powers:
        n_h = 0
        n_oh = 0
        n_oh_nc = 0

        for h, oh, crit in lines:
            dh = coefficient * -sp
            dh_c = dh

            oh_nc = oh

            if crit:
                # scale spell power differential by 1.5 if spell was a crit
                dh_c *= 1.5

                # Scale oh down
                oh_nc = oh - (h - h / 1.5)

            # remove spell power contribution
            h -= dh_c
            oh -= dh_c
            oh_nc -= dh

            if h < 0.0:
                # could happen for heals on healing reduced players, we just ignore these for now
                continue

            n_h += 1
            # n_h_nc += not_crit

            if oh > 0.0:
                n_oh += 1

            if oh_nc > 0.0:
                n_oh_nc += 1

        n_heals.append(n_h)
        n_overheals.append(n_oh)

        n_overheals_nc.append(n_oh_nc)

    # plot probabilities
    plot_oh_prob(
        player_name,
        spell_id,
        spell_powers,
        sp_extrap,
        sp_shift,
        n_heals,
        n_overheals,
        n_overheals_nc,
    )


def main(
    player, source, spell_power=500, ignore_crit=False, spell_id=None, **kwargs
):
    heal_lines, periodics, absorbs = read_heals(player, source, **kwargs)

    # Group lines
    heal_lines = group_processed_lines(heal_lines, ignore_crit, spell_id=spell_id)
    for spell_id, lines in heal_lines.items():
        spell_overheal_probability(player, spell_id, lines, spell_power)


if __name__ == "__main__":
    from backend.parser import OverhealParser

    # Make plot dirs
    import os
    os.makedirs("figs/probability/likelihood", exist_ok=True)

    parser = OverhealParser(
        description="""Plots probability of overheals for different spells.""",
        need_player=True,
        accept_spell_id=True,
        accept_spell_power=True,
    )

    parser.add_argument(
        "--ignore_crit", action="store_true", help="Remove critical heals from analysis"
    )

    args = parser.parse_args()

    main(**vars(args))
