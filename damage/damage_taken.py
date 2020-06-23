"""
Functions for tracking damage taken by raid or character.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""


def _get_net_health_change(e, current_deficit):
    """Get the net health change, accounting for mitigation, overheal and overkill."""
    gross = e[7]
    over = e[8]
    overkill = e[9]
    overheal = gross > 0 and over > 0

    if overkill < 0:
        gross -= overkill

    if gross > 0:
        # healing, then heal min of gross and current deficit
        net = min(gross, -current_deficit)
    else:
        # damage, remove mitigated damage
        net = min(gross - over, -current_deficit)

    return net, overheal, overkill


def character_damage_taken(events, character_name, verbose=False):
    times = []
    health_pcts = []
    deficits = []
    nets = []
    health_diffs = []
    health_ests = []
    deficit = 0

    for e in events:
        if e.target != character_name:
            continue

        net, overheal, _ = _get_net_health_change(e, deficit)

        nets.append(net)
        deficit += net

        if overheal:
            # overheal, at max health
            deficit = 0

        if deficit > 0:
            deficit = 0

        # estimate total health from deficit and %health
        # health = max_health * %health = max_health - deficit
        # max_health * (1 - %health) = deficit
        health_pct = e.health_pct
        if health_pct < 100:
            health_est = -deficit / (1.0 - health_pct / 100)
        else:
            health_est = None

        t = e.timestamp.total_seconds()
        if verbose:
            print(t, deficit)

        times.append(t)
        health_pcts.append(health_pct - 100)
        deficits.append(deficit)
        health_diffs.append(net)
        health_ests.append(health_est)

    return times, deficits, nets, health_pcts, health_ests


def raid_damage_taken(events, character_name=None, verbose=False):
    # for each character
    times = dict(all=[])
    health_pcts = dict(all=[])
    deficits = dict(all=[])
    deficits_time = []
    health_diffs = dict(all=[])
    health_ests = dict(all=[])
    deficit = dict()
    all_deficit = 0

    death_times = dict()
    min_deficit = 0
    min_deficits = []

    name_dict = dict()

    for e in events:

        target_id = e.target_id
        if target_id not in name_dict:
            name_dict[target_id] = e.target

        if target_id not in times:
            times[target_id] = []
            health_pcts[target_id] = []
            deficits[target_id] = []
            health_diffs[target_id] = []
            health_ests[target_id] = []
            deficit[target_id] = 0

        current_deficit = deficit[target_id]
        net, overheal, overkill = _get_net_health_change(e, current_deficit)

        source = e.source
        if source == character_name:
            # if character name is specified, ignore all heals from that character
            net = min(0, net)

        current_deficit += net
        all_deficit += net

        timestamp = e.timestamp
        if target_id in death_times and timestamp > death_times[target_id]:
            print(f"Dead {e.target} participating again, assuming Ankh or Soulstone used.")

            del death_times[target_id]

            # Recalculate min deficit
            dead_deficits = list(deficits[character_id][-1] for character_id in death_times.keys())
            min_deficit = sum(dead_deficits)

        if overkill < 0:
            # someone died, lower raid min deficit
            print(f"{e.target} died, {current_deficit} deficit, {-overkill} overkill")
            death_times[target_id] = timestamp

        # if (overheal and current_deficit < 0) or current_deficit > 0:
        #     print(f"{target} got overhealed with {current_deficit} deficit.")
        #     all_deficit -= current_deficit
        #     current_deficit = 0

        if current_deficit > 0:
            all_deficit -= current_deficit
            current_deficit = 0

        t = timestamp.total_seconds()

        # estimate total health from deficit and %health
        # health = max_health * %health = max_health - deficit
        # max_health * (1 - %health) = deficit
        health_pct = e.health_pct
        if health_pct < 100:
            health_est = -current_deficit / (1.0 - health_pct / 100)
        else:
            health_est = None

        times[target_id].append(t)
        deficits[target_id].append(current_deficit)
        deficit[target_id] = current_deficit

        health_pcts[target_id].append(health_pct - 100)
        health_diffs[target_id].append(net)
        health_ests[target_id].append(health_est)

        times["all"].append(t)
        deficits["all"].append(all_deficit)
        health_diffs["all"].append(net)

        if verbose:
            print(t, all_deficit)

        # update min deficit
        if target_id in death_times.keys():
            dead_deficits = (deficits[character_id][-1] for character_id in death_times.keys())
            min_deficit = sum(dead_deficits)

        min_deficits.append(min_deficit)

        deficit_time = {k: deficit[k] if k not in death_times else 0 for k in deficit}
        deficits_time.append(deficit_time)

    return times, deficits, deficits_time, name_dict, min_deficits
