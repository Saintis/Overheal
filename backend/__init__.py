"""
Collection of general functions for managing logs data.

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

    for time_stamp, source, spell_id, target, total_heal, overheal, is_crit in processed_lines:
        if ignore_crit and is_crit:
            continue

        if filter_spell_id and spell_id != filter_spell_id:
            continue

        if spell_id not in spell_dict:
            spell_dict[spell_id] = []

        spell_dict[spell_id].append((total_heal, overheal, is_crit))

    return spell_dict
