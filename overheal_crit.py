"""
Script that estimates value of 1% crit.

By: Filip Gokstorp (Saintis), 2020
"""
import read_from_raw as raw
import read_from_wcl as wcl
import spell_data as sd
from overheal_table import group_processed_lines


def process_spell(spell_id, spell_lines):
    n_spells = len(spell_lines)

    crit_underheal = []
    crit_fullheal = []

    hh = 0
    ohh = 0

    for h, oh, crit in spell_lines:
        # we only care about crits
        hh += h
        ohh += oh

        if not crit:
            continue

        ch = h * (1 / 3)
        cuh = max(0.0, ch - oh)

        crit_fullheal.append(ch)
        crit_underheal.append(cuh)

    n_crits = len(crit_underheal)

    if n_crits == 0:
        crit_fh = 0
        crit_uh = 0
    else:
        crit_fh = sum(crit_fullheal) / n_crits
        crit_uh = sum(crit_underheal) / n_crits

    return (spell_id, n_crits, n_spells, crit_fh, crit_uh, hh, ohh)


def print_results(data):
    if len(data) == 0:
        print("No data found.")
        return

    data = sorted(data, key=lambda d: sd.spell_name(d[0]))

    print(f"Crits:")

    nn_crits = 0
    nn_spells = 0
    s_crit_fh = 0
    s_crit_uh = 0
    s_coef = 0
    t_hh = 0
    t_oh = 0

    for spell_id, n_crits, n_spells, crit_fh, crit_uh, hh, ohh in data:
        spell_name = sd.spell_name(spell_id)
        coef = sd.spell_coefficient(spell_id)

        nn_crits += n_crits
        nn_spells += n_spells
        s_crit_fh += crit_fh * n_crits
        s_crit_uh += crit_uh * n_crits
        s_coef += coef * n_crits
        t_hh += hh
        t_oh += ohh

        crit_pc = n_crits / n_spells

        message = (
            f"  {spell_name:<30s}: {n_crits:3d} / {n_spells:3d} crits ({crit_pc:5.1%}); ({ohh / hh:5.1%} OH)"
        )

        if n_crits == 0:
            print(message)
            continue

        crit_oh = crit_fh - crit_uh
        oh_pc = crit_oh / crit_fh

        crit_heal = 0.01 * crit_uh
        eq_h_0c = crit_heal / coef
        eq_h = eq_h_0c / (1.0 + 0.5 * crit_pc)

        message += f", Crit H: {crit_fh:4.0f} ({crit_uh:4.0f} + {crit_oh:4.0f} oh)  ({oh_pc:5.1%} oh)"
        message += f", 1% crit gives {0.01 * crit_uh:+4.1f} healing eq to {eq_h:+5.1f} h ({eq_h_0c:+5.1f} at 0% crit)."

        print(message)

    print("")
    crit_pc = nn_crits / nn_spells

    spell_name = "Overall / Average"
    coef = s_coef / nn_crits

    message = (
        f"  {spell_name:<30s}: {nn_crits:3d} / {nn_spells:3d} crits ({crit_pc:5.1%}); ({t_oh / t_hh:5.1%} OH)"
    )

    if nn_crits == 0:
        print(message)
        return

    crit_fh = s_crit_fh / nn_crits
    crit_uh = s_crit_uh / nn_crits

    crit_oh = crit_fh - crit_uh
    oh_pc = crit_oh / crit_fh

    crit_heal = 0.01 * crit_uh
    eq_h_0c = crit_heal / coef
    eq_h = eq_h_0c / (1.0 + 0.5 * crit_pc)

    message += f", Crit H: {crit_fh:4.0f} ({crit_uh:4.0f} + {crit_oh:4.0f} oh)  ({oh_pc:5.1%} oh)"
    message += f", 1% crit gives {0.01 * crit_uh:+4.1f} healing eq to {eq_h:+5.1f} h ({eq_h_0c:+5.1f} at 0% crit)."

    print(message)


def main(args):
    player_name = args.player_name
    log_file = args.log_file
    spell_id = args.spell_id
    url = args.url

    if "https://" in log_file or "http://" in log_file:
        url = log_file

    if url:
        heal_lines = wcl.read_from_url(url)
    else:
        log_lines = raw.get_lines(log_file)
        heal_lines, _ = raw.get_heals(player_name, log_lines)

    # Group lines
    heal_lines = group_processed_lines(heal_lines, False, spell_id=spell_id)

    data = []

    if spell_id:
        lines = []
        # Only one will be populated
        if spell_id in heal_lines:
            lines = heal_lines[spell_id]
        else:
            print(f"Could not find casts of spell [{spell_id}]")
            exit(1)

        data.append(process_spell(spell_id, lines))
    else:
        for spell_id, lines in heal_lines.items():
            data.append(process_spell(spell_id, lines))

    print_results(data)


if __name__ == "__main__":
    import os
    import argparse

    # make sure directories exist
    os.makedirs("figs/crit", exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Analyses log and estimates healing of crits. Counts up the healing and overhealing done by each "
        "found crit. Prints out extra healing done by each crit on average and the equivalent +heal worth "
        "for each spell, and for the average spell profile over the whole combat log."
    )

    parser.add_argument("player_name", help="Player name to analyse overheal for")
    parser.add_argument("log_file", help="Path to the log file to analyse")
    parser.add_argument("--spell_id", type=str, help="Spell id to filter for")
    parser.add_argument(
        "-u", "--url", action="store_true", help="Tells scripts that the provided logfile is a WCL link."
    )

    args = parser.parse_args()

    main(args)
