"""
Script that estimates spell cumulative distribution function of overheal chance.

By: Filip Gokstorp (Saintis), 2020
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from readers import read_heals
from backend import group_processed_lines
from backend.parser import OverhealParser

import spell_data as sd


def process_spell(player_name, spell_id, spell_lines, spell_power=None, show=True, path=None):
    spell_name = sd.spell_name(spell_id)

    relative_underheal = []
    is_crit = []

    for h, oh, crit in spell_lines:
        relative_underheal.append(1.0 - oh / h)
        is_crit.append(1 if crit else 0)

    cast_fraction = np.linspace(0, 1, len(relative_underheal))

    relative_underheal = np.array(relative_underheal)
    relative_underheal = np.sort(relative_underheal)
    # is_crit = np.array(is_crit)

    plt.figure(constrained_layout=True)
    plt.fill_between(cast_fraction, relative_underheal, label="Underheal")
    plt.fill_between(cast_fraction, 1, relative_underheal, label="Overheal")

    # add base heal line if spell-power is included

    base_heal = sd.spell_heal(spell_id)
    coeff = sd.spell_coefficient(spell_id)

    if spell_power and base_heal > 0 and coeff > 0:
        extra_heal = coeff * spell_power
        base_heal_fraction = base_heal / (base_heal + extra_heal)

        plt.axhline(base_heal_fraction, linestyle="--", color="k", label="Base heal")

    plt.title(f"{spell_name}, {len(spell_lines)} casts")
    plt.xlabel("Fraction of casts")
    plt.ylabel("Fraction of heal (orange overheal, blue underheal)")
    plt.xlim((0, 1))
    plt.ylim((0, 1))
    plt.legend()

    if path is None:
        path = "figs/cdf"

    plt.savefig(f"{path}/{player_name}_cdf_{spell_id}.png")

    # plt.figure(constrained_layout=True)
    # plt.fill_between(relative_underheal, 1 - cast_fraction, label="Underheal")
    # plt.fill_between(relative_underheal, 1, 1 - cast_fraction, label="Overheal")

    # plt.title(spell_name)
    # plt.ylabel("Fraction of casts")
    # plt.xlabel("Fraction of overheals (orange overheal, blue underheal)")
    # plt.xlim((0, 1))
    # plt.ylim((0, 1))
    # plt.legend()

    if show:
        plt.show()


def overheal_cdf(source, character_name, spell_id=None, path=None, **kwargs):

    # make sure directories exist
    if path is None:
        path = "figs/cdf"

    os.makedirs(path, exist_ok=True)

    heal_lines, periodic_lines, absorbs = read_heals(source, character_name=character_name, **kwargs)

    # Group lines
    heal_lines = group_processed_lines(heal_lines, False, spell_id=spell_id)
    periodic_lines = group_processed_lines(periodic_lines, False, spell_id=spell_id)

    if spell_id:
        lines = []
        # Only one will be populated
        if spell_id in heal_lines:
            lines = heal_lines[spell_id]
        elif spell_id in periodic_lines:
            lines = periodic_lines[spell_id]
        else:
            print(f"Could not find casts of spell [{spell_id}]")
            exit(1)

        process_spell(character_name, spell_id, lines, **kwargs)
    else:
        for spell_id, lines in heal_lines.items():
            process_spell(character_name, spell_id, lines, show=False, path=path, **kwargs)
        for spell_id, lines in periodic_lines.items():
            process_spell(character_name, spell_id, lines, show=False, path=path, **kwargs)


def main():
    parser = OverhealParser(
        description="Analyses logs and gives overheal cdf.",
        need_character=True,
        accept_spell_id=True,
        accept_spell_power=True
    )
    parser.add_argument("--path", help="Path to output figures too.", default="figs/cdf")
    args = parser.parse_args()

    path = args.path

    overheal_cdf(args.source, args.character_name, args.spell_id, path)


if __name__ == "__main__":
    main()
