"""
Python script for getting a summary plot of heals and their overheal fraction.

By: Filip Gokstorp (Saintis), 2020
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from src import readers
from src import group_processed_lines
import spell_data as sd


def process_spell(spell_id, spell_lines, spell_power=None):
    base_heal = sd.spell_heal(spell_id)
    coeff = sd.spell_coefficient(spell_id)

    if base_heal == 0 or coeff == 0:
        return

    if spell_power is None:
        spell_power = 700.0

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


def overheal_summary(source, character_name, spell_power, path=None, show=False, encounter=None):
    # log_lines = raw.get_lines(log_file)
    # heal_lines, periodic_lines, _ = read_heals(source, character_name=character_name)

    processor = readers.get_processor(source, character_name=character_name)
    encounter = processor.select_encounter(encounter=encounter)

    processor.process(encounter=encounter)
    heal_lines = processor.heals

    if path is None:
        path = "figs"

    os.makedirs(path, exist_ok=True)

    # Group lines
    heal_lines = group_processed_lines(heal_lines, False)
    # periodic_lines = group_processed_lines(periodic_lines, False)

    labels = []

    nn_underheal = []
    nn_overheal = []
    nn_downrank = []
    nn_drop_h = []

    for spell_id, lines in heal_lines.items():
        labels.append(sd.spell_name(spell_id))

        data = process_spell(spell_id, lines, spell_power)

        if not data:
            continue

        n_heal, n_underheal, n_overheal, n_downrank, n_drop_h = data

        nn_underheal.append(n_underheal / n_heal)
        nn_overheal.append(n_overheal / n_heal)
        nn_downrank.append(n_downrank / n_heal)
        nn_drop_h.append(n_drop_h / n_heal)

    # for spell_id, lines in periodic_lines.items():
    #     labels.append(sd.spell_name(spell_id))
    #     data = process_spell(spell_id, lines, spell_power)
    #
    #     if not data:
    #         continue
    #
    #     n_heal, n_underheal, n_overheal, n_downrank, n_drop_h = data
    #
    #     nn_underheal.append(n_underheal / n_heal)
    #     nn_overheal.append(n_overheal / n_heal)
    #     nn_downrank.append(n_downrank / n_heal)
    #     nn_drop_h.append(n_drop_h / n_heal)

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
    plt.bar(labels, nn_drop_h, color="yellow", bottom=b0, label="Partial OH, less than +heal")
    plt.bar(labels, nn_downrank, color="orange", bottom=b1, label="Partial OH, more than +heal")
    plt.bar(labels, nn_overheal, color="red", bottom=b2, label="Full overheal")

    if encounter:
        title = f"{character_name}: {encounter.boss}"
    else:
        title = character_name

    plt.title(title)
    plt.ylabel("Fraction of casts")
    plt.xticks(rotation=90)
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    plt.savefig(f"{path}/{character_name}_summary.png")

    if show:
        plt.show()

    plt.close()


def main(argv=None):
    from src.parser import OverhealParser

    parser = OverhealParser(
        description="Analyses logs and gives summary plot.",
        need_character=True,
        accept_spell_power=True,
        accept_encounter=True,
    )
    parser.add_argument("--path")
    parser.add_argument("--show", action="store_true")

    args = parser.parse_args(argv)

    overheal_summary(
        args.source,
        args.character_name,
        spell_power=args.spell_power,
        path=args.path,
        show=args.show,
        encounter=args.encounter,
    )


if __name__ == "__main__":
    main()
