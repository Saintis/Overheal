"""
Python script for getting a summary plot of heals and their overheal fraction.

By: Filip Gokstorp (Saintis), 2020
"""
import numpy as np
import matplotlib.pyplot as plt

from readers import read_heals
from backend import group_processed_lines
import spell_data as sd


def process_spell(spell_id, spell_lines, spell_power):
    base_heal = sd.spell_heal(spell_id)
    coeff = sd.spell_coefficient(spell_id)

    if base_heal == 0 or coeff == 0:
        return

    extra_heal = coeff * spell_power
    base_heal_fraction = base_heal / (base_heal + extra_heal)

    n_heal = 0
    n_underheal = 0
    n_overheal = 0
    n_downrank = 0
    n_drop_h = 0

    for h, oh, crit in spell_lines:
        h_fraction = 1.0 - oh / h

        n_heal += 1

        if h_fraction >= 1:
            n_underheal += 1
        elif h_fraction <= 0:
            n_overheal += 1
        elif h_fraction < base_heal_fraction:
            n_downrank += 1
        else:
            n_drop_h += 1

    return n_heal, n_underheal, n_overheal, n_downrank, n_drop_h


def main(player_name, source, spell_power):
    # log_lines = raw.get_lines(log_file)
    heal_lines, periodic_lines, _ = read_heals(player_name, source)

    # Group lines
    heal_lines = group_processed_lines(heal_lines, False)
    periodic_lines = group_processed_lines(periodic_lines, False)

    labels = []

    nn_underheal = []
    nn_overheal = []
    nn_downrank = []
    nn_drop_h = []

    for spell_id, lines in heal_lines.items():
        labels.append(sd.spell_name(spell_id))
        n_heal, n_underheal, n_overheal, n_downrank, n_drop_h = process_spell(
            spell_id, lines, spell_power
        )

        nn_underheal.append(n_underheal / n_heal)
        nn_overheal.append(n_overheal / n_heal)
        nn_downrank.append(n_downrank / n_heal)
        nn_drop_h.append(n_drop_h / n_heal)

    for spell_id, lines in periodic_lines.items():
        labels.append(sd.spell_name(spell_id))
        n_heal, n_underheal, n_overheal, n_downrank, n_drop_h = process_spell(
            spell_id, lines, spell_power
        )

        nn_underheal.append(n_underheal / n_heal)
        nn_overheal.append(n_overheal / n_heal)
        nn_downrank.append(n_downrank / n_heal)
        nn_drop_h.append(n_drop_h / n_heal)

    ii = np.argsort(nn_underheal)

    labels = np.array(labels)[ii]
    nn_overheal = np.array(nn_overheal)[ii]
    nn_underheal = np.array(nn_underheal)[ii]
    nn_downrank = np.array(nn_downrank)[ii]
    nn_drop_h = np.array(nn_drop_h)[ii]

    b0 = nn_underheal
    b1 = b0 + nn_drop_h
    b2 = b1 + nn_downrank

    plt.figure(figsize=(8, 6), constrained_layout=True)
    plt.bar(labels, nn_underheal, color="green", label="Underheal")
    plt.bar(
        labels,
        nn_drop_h,
        color="yellow",
        bottom=b0,
        label="Partial OH, less than +heal",
    )
    plt.bar(
        labels,
        nn_downrank,
        color="orange",
        bottom=b1,
        label="Partial OH, more than +heal",
    )
    plt.bar(labels, nn_overheal, color="red", bottom=b2, label="Full overheal")

    plt.ylabel("Fraction of casts")
    plt.xticks(rotation=90)
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    plt.savefig(f"figs/{player_name}_summary.png")
    plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyses logs and gives summary plot."
    )

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument(
        "spell_power", type=int, help="Spell power for base heal fraction calculation"
    )

    args = parser.parse_args()

    main(args.player_name, args.log_file, args.spell_power)
