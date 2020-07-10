"""
Backend / source functionality for the overheal analysis.

By: Filip Gokstorp (Saintis), 2020
"""


def group_processed_lines(processed_lines, ignore_crit, spell_id=None):
    """
    Groups processed lines by spell id.

    :param processed_lines: groups lines by spell id.
    :param ignore_crit: if true, filters out crits
    :param spell_id: spell id to filter for
    :returns a dictionary by spell id, with a list of (heal, overheal, is_crit)
    """
    spell_dict = dict()

    filter_spell_id = spell_id

    for event in processed_lines:
        spell_id = event.spell_id
        if filter_spell_id and spell_id != filter_spell_id:
            continue

        is_crit = event.is_crit
        if ignore_crit and is_crit:
            continue

        if spell_id not in spell_dict:
            spell_dict[spell_id] = []

        spell_dict[spell_id].append((event.total_heal, event.overheal, is_crit))

    return spell_dict
