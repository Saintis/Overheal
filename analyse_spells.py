"""
Analyse spells for an encounter

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
import numpy as np
import matplotlib.pyplot as plt
import json

from readers import read_from_raw as raw
from backend.parser import OverhealParser
from backend import encounter_picker, get_player_name, get_time_stamp

import spell_data as sd


def get_casts(character_name, log_lines):
    """Get spell casts and time stamps for specified character in lines."""

    spell_casts = []
    spell_heals = []
    spell_periodics = []
    spell_absorbs = []

    for line in log_lines:
        line_parts = line.split(",")
        length = len(line_parts)

        if "SPELL_CAST_SUCCESS" in line_parts[0]:
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            spell_time = get_time_stamp(line_parts[0])
            spell_id = line_parts[9]
            spell_casts.append((spell_time, spell_id))

        elif "SPELL_HEAL" in line_parts[0]:
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            spell_id = line_parts[9]
            heal_amount = int(line_parts[29])  # total heal
            overheal_amount = int(line_parts[30])  # total heal
            is_crit = "1" in line_parts[-1]
            spell_heals.append((spell_id, heal_amount, overheal_amount, is_crit, True))

        elif "SPELL_PERIODIC_HEAL" in line_parts[0]:
            source = get_player_name(line_parts[2])

            if character_name != source:
                continue

            spell_id = line_parts[9]
            heal_amount = int(line_parts[29])  # total heal
            overheal_amount = int(line_parts[30])  # total heal
            spell_periodics.append((spell_id, heal_amount, overheal_amount, False, False))

        elif "SPELL_ABSORBED" in line_parts[0]:
            if length == 18:
                source = line_parts[10]
            else:
                source = line_parts[13]

            source = get_player_name(source)

            if character_name != source:
                continue

            spell_id = line_parts[13 if length == 18 else 16]
            abs_amount = int(line_parts[16 if length == 18 else 19])  # absorb amount
            spell_absorbs.append((spell_id, abs_amount, 0, False, False))

    return spell_casts, spell_heals, spell_periodics, spell_absorbs


def group_spells(spell_casts, spell_heals, spell_periodics, spell_absorbs, reduce_crits=False, neg_sp=0.0):
    spell_dict = {}

    for _, spell_id in spell_casts:
        if spell_id not in spell_dict:
            spell_dict[spell_id] = dict(casts=0, heals=0, gross_heal=0, overheal=0, crits=0, can_crit=0)

        spell_dict[spell_id]["casts"] += 1

    for spell_id, th, oh, is_crit, can_crit in spell_heals + spell_periodics + spell_absorbs:
        if spell_id == "27805":
            # holy nova pairs with different cast id
            spell_id = "27801"

        spell = spell_dict[spell_id]
        spell["heals"] += 1

        dhp = neg_sp * sd.spell_coefficient(spell_id)

        if can_crit:
            spell["can_crit"] = 1

        if is_crit:
            spell["crits"] += 1

            if reduce_crits:
                dh = th / 3
                th -= dh
                oh = max(0, oh - dh)
            else:
                dhp *= 1.5

        th = max(0, th - dhp)
        oh = max(0, oh - dhp)

        spell["gross_heal"] += th
        spell["overheal"] += oh

    return spell_dict


def sum_spells(spells, talents=None):
    total_data = dict(
        casts=0, gross_heal=0, overheal=0, net_heal=0, mana=0, coef=0, crit_coef=0, crit_heal=0, crits=0, can_crit=0
    )
    spell_data = dict()

    for spell_id, spell in spells.items():
        casts = spell["casts"]
        gross_heal = spell["gross_heal"]
        overheal = spell["overheal"]
        crits = spell["crits"]
        can_crit = spell["can_crit"]

        if gross_heal == 0:
            mana = sd.spell_mana(spell_id, talents, warn_on_not_found=False)
            if mana == 0:
                continue
        else:
            mana = sd.spell_mana(spell_id, talents)

        net_heal = gross_heal - overheal
        average_net_heal = net_heal / casts

        coef = sd.spell_coefficient(spell_id, warn_on_not_found=True)

        if "Renew" in sd.spell_name(spell_id):
            coef *= 5

        spell_data[spell_id] = dict(
            spell, mana=mana, net_heal=average_net_heal, coef=coef, crit_heal=0.5 * can_crit * gross_heal / casts
        )

        total_data["casts"] += casts
        total_data["gross_heal"] += gross_heal
        total_data["overheal"] += overheal
        total_data["net_heal"] += net_heal
        total_data["mana"] += casts * mana
        total_data["coef"] += casts * coef
        total_data["crit_coef"] += casts * coef + crits * coef * 0.5
        total_data["crit_heal"] += 0.5 * gross_heal * can_crit
        total_data["crits"] += crits
        total_data["can_crit"] += casts * can_crit

    return total_data, spell_data


def analyse_spell(source, character_name, encounter=None, reduce_crits=False, spell_power=None, **_):
    if spell_power is None:
        spell_power = 0

    log = raw.get_lines(source)
    encounter, encounter_lines, encounter_start, encounter_end = encounter_picker(log, encounter)

    print()
    print(f"Analysis for {encounter}:")
    print()

    try:
        with open("me.json") as fp:
            me = json.load(fp)
            talents = me["talents"]
            gear = me["gear"]
    except FileNotFoundError:
        talents = {"Meditation": 0, "Spiritual Guidance": 0}
        gear = {"3T2": False}

    spell_casts, spell_heals, spell_periodics, spell_absorbs = get_casts(character_name, encounter_lines)
    all_spells = group_spells(
        spell_casts, spell_heals, spell_periodics, spell_absorbs, reduce_crits=reduce_crits, neg_sp=spell_power
    )

    del all_spells["10901"]

    total_data, spell_data = sum_spells(all_spells, talents)
    spells = sorted(spell_data.items(), key=lambda x: sd.spell_name(x[0], warn_on_not_found=False))

    for spell_id, spell in spells:
        name = sd.spell_name(spell_id)
        casts = spell["casts"]
        mana = spell["mana"]
        net_heal = spell["net_heal"]
        hpm = net_heal / mana
        coef = spell["coef"]
        crits = spell["crits"]
        crit_heal = spell["crit_heal"]

        print(
            f"{name+':':29s} {casts:4d} {mana:4.0f} mpc  {net_heal:4.0f} hpc {hpm:5.2f} hpm  {coef:.3f}"
            f"  {crits / casts:6.2%}  {crit_heal:3.0f}"
        )

    casts = total_data["casts"]
    crits = total_data["crits"]
    can_crit = total_data["can_crit"]
    mana = total_data["mana"]

    gross_heal = total_data["gross_heal"]
    net_heal = total_data["net_heal"]
    crit_heal = total_data["crit_heal"]

    g_coef = total_data["coef"]
    c_coef = total_data["crit_coef"]

    crit_rate = crits / can_crit

    # reduced sp data
    dh = 20.0
    all_spells = group_spells(
        spell_casts, spell_heals, spell_periodics, spell_absorbs, reduce_crits=reduce_crits, neg_sp=dh
    )
    del all_spells["10901"]
    total_data, _ = sum_spells(all_spells, talents)
    dheal = net_heal - total_data["net_heal"]
    n_coef = dheal / dh

    print()
    print(
        f"{'Average:':29s} {casts:4d} {mana/casts:4.0f} mpc  {net_heal/casts:4.0f} hpc "
        f"{net_heal/mana:5.2f} hpm  {n_coef/casts:.3f}  {crit_rate:.2%}  {c_coef/casts:.3f}"
    )
    print(f"Coefficient {n_coef/casts:.3f}  ({g_coef/casts:.3f})  {1.0 - n_coef / g_coef:.0%} reduction")
    print()

    encounter_length = (encounter_end - encounter_start).total_seconds()

    gross_hps = gross_heal / encounter_length
    net_hps = net_heal / encounter_length

    gross_hpm = gross_heal / mana
    net_hpm = net_heal / mana

    print(f"  Fight duration:  {encounter_length:.1f}s")
    print()
    print(f"  Gross heal: {gross_heal:,.0f}")
    print(f"  Net heal:   {net_heal:,.0f}")
    print(f"  Used mana:  {mana:,.0f}")
    print()
    print(f"  Heal coef:  {n_coef:.2f}  ({g_coef:.2f}, {c_coef:.2f})")

    print()

    print(f"  HPS:  {net_hps:.1f}  ({gross_hps:.1f})")
    print(f"  HPM:  {net_hpm:.3f}  ({gross_hpm:.3f})")
    print(f"  VPM:  {net_hpm / n_coef:.3f}  ({gross_hpm / g_coef:.3f}, {gross_hpm / c_coef:.3f})")

    print()

    combat_regen = talents.get("Meditation", 0) * 0.05
    if gear.get("3T2", False):
        combat_regen += 0.15

    mana_per_spirit = combat_regen * (1 / 4) * (encounter_length / 2)
    hp_per_spirit = talents.get("Spiritual Guidance", 0) * 0.05
    crit_per_int = 1 / 60
    mana_per_int = 15.0 * (1.0 + talents.get("Mental Strength") * 0.02)

    # print(f"  {1 / (mana_per_spirit / encounter_length * 5):.2f} Spirit = 1 mp5")
    # print()

    heal_hp = n_coef
    heal_mp5 = encounter_length / 5 * net_hpm
    heal_spirit = mana_per_spirit * net_hpm + hp_per_spirit * heal_hp
    heal_crit = 0.01 * crit_heal
    heal_int = mana_per_int * net_hpm + crit_per_int * heal_crit

    g_heal_hp = c_coef
    g_heal_mp5 = (encounter_length / 5) * gross_hpm
    g_heal_spirit = mana_per_spirit * gross_hpm + hp_per_spirit * g_heal_hp
    g_heal_crit = 0.01 * crit_heal
    g_heal_int = mana_per_int * gross_hpm + crit_per_int * g_heal_crit

    print(f"    Int,   Spi,   +hp,   mp5,  crit")
    print(f"  {heal_int:5.1f}, {heal_spirit:5.1f}, {heal_hp:5.1f}, {heal_mp5:5.1f}, {heal_crit:5.1f}")
    print(
        f"  {heal_int/heal_hp:5.4g}, {heal_spirit/heal_hp:5.3f}, 1.000, {heal_mp5/heal_hp:5.4g}, {heal_crit/heal_hp:5.4g}"
    )
    print()
    print(
        f" ({g_heal_int:5.4g},"
        f" {g_heal_spirit:5.4g},"
        f" {g_heal_hp:5.4g},"
        f" {g_heal_mp5:5.4g},"
        f" {g_heal_crit / (1.0 + crit_rate):5.4g})"
    )
    print(
        f" ({g_heal_int/g_heal_hp:5.4g},"
        f" {g_heal_spirit/g_heal_hp:5.4g},"
        f" 1.000,"
        f" {g_heal_mp5/g_heal_hp:5.4g},"
        f" {g_heal_crit/g_heal_hp:5.4g})"
    )

    print()


def main(argv=None):
    parser = OverhealParser(
        description="Analyses an encounter and prints information about the spells used.",
        need_character=True,
        accept_spell_power=True,
        accept_encounter=True
    )
    parser.add_argument("-r", "--reduce_crits", action="store_true")

    args = parser.parse_args(args=argv)

    analyse_spell(args.source, args.character_name, spell_power=args.spell_power, encounter=args.encounter)


if __name__ == "__main__":
    main()
