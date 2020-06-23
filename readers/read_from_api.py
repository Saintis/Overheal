"""
Read data from WCL API.

By: Filip Gokstorp (Saintis), 2020
"""
import os
import requests
from json.decoder import JSONDecodeError
from datetime import datetime

from .event_types import HealEvent, DamageTakenEvent

# First try environment key
API_KEY = os.environ.get("WCL_API_KEY", None)
if API_KEY is None:
    # Otherwise try to read from file
    try:
        API_KEY = open("apikey.txt", "r").read().strip()
    except FileNotFoundError:
        print("API key not found. Please save in a plain text file called `apikey.txt`.")
        exit(100)


API_ROOT = "https://classic.warcraftlogs.com:443/v1"


class ProgressBar:
    """Simple CLI progress bar"""

    def __init__(self, end, length=70):
        self.end = end
        self.length = length

    def render(self, progress):
        """Render the progress bar"""
        assert progress >= 0, "Progress must be positive"

        pct = progress / self.end
        n_bars = int(pct * self.length)
        bars = "=" * n_bars
        if n_bars < self.length:
            bars += ">"

        return f"[{bars:70s}]  {pct:4.0%}  {progress:8d} / {self.end:8d}"


def _get_api_request(url):
    """
    Get an API request and check status code.

    :param url: full url with request details to use.
    """
    req = requests.get(url)

    if not req.status_code == 200:
        print("Error getting API request:", url)
        print("Status code:", req.status_code)
        print("Error:", req.text)
        exit(200)

    data = None
    try:
        data = req.json()
    except JSONDecodeError:
        print("WarcraftLogs did not return proper JSON, it is likely down for maintenance.")
        print("Request response:", req.text)
        exit(300)

    return data


def get_fights(code):
    url = f"{API_ROOT}/report/fights/{code}?api_key={API_KEY}"
    return _get_api_request(url)


def get_player_names(code):
    fight_data = get_fights(code)

    friendlies = fight_data["friendlies"]
    player_names = dict()

    for f in friendlies:
        player_id = f["id"]
        player_name = f["name"]
        player_names[player_id] = player_name

    return player_names


def _get_heals(code, start=0, end=None, names=None, for_player=None):
    """Gets all heals for the log"""

    if end is None:
        end = start + 3 * 60 * 60 * 1000  # look at up to 3h of data

    if names is None:
        names = dict()

    heals = []
    periodics = []
    absorbs = []

    next_start = start

    print("Fetching healing events from WCL...")
    progress_bar = ProgressBar(end - start, length=70)

    # will have to loop to get results
    request_more = True
    while request_more:
        url = f"{API_ROOT}/report/events/healing/{code}?start={next_start}&end={end}&api_key={API_KEY}"

        print(progress_bar.render(next_start - start), end="\r")

        data = _get_api_request(url)
        events = data["events"]
        if "nextPageTimestamp" in data:
            next_start = data["nextPageTimestamp"]
        else:
            request_more = False

        for e in events:
            try:
                timestamp = e["timestamp"]
                timestamp = datetime.fromtimestamp(timestamp / 1000.0).time()
                spell_id = str(e["ability"]["guid"])

                if "sourceID" not in e:
                    # heal not from a player, skipping
                    continue

                source_id = e["sourceID"]
                source = names.get(source_id, f"[pid {source_id}]")

                if for_player and source != for_player:
                    continue

                target_id = e["targetID"]
                target = names.get(target_id, f"[pid {target_id}]")
                health_pct = e.get("hitPoints", None)
                # event_type = e["type"]

                amount = e["amount"]

                if e["type"] == "absorbed":
                    # Shield absorb
                    event = HealEvent(
                        timestamp, source, source_id, spell_id, target, target_id, health_pct, amount, 0, False
                    )
                    absorbs.append(event)
                    continue

                overheal = e.get("overheal", 0)

                if e.get("tick"):
                    # Periodic tick
                    event = HealEvent(
                        timestamp,
                        source,
                        source_id,
                        spell_id,
                        target,
                        target_id,
                        health_pct,
                        amount + overheal,
                        overheal,
                        False,
                    )
                    periodics.append(event)
                    continue

                is_crit = e.get("hitType", 1) == 2

                event = HealEvent(
                    timestamp,
                    source,
                    source_id,
                    spell_id,
                    target,
                    target_id,
                    health_pct,
                    amount + overheal,
                    overheal,
                    is_crit,
                )
                heals.append(event)
            except Exception as ex:
                print("Exception while handling line", e)
                print(ex)

    print(progress_bar.render(end - start))

    return heals, periodics, absorbs


def _get_damage(code, start=0, end=None, names=None, for_player=None):
    """Gets all heals and damage events for the log"""

    if end is None:
        end = start + 3 * 60 * 60 * 1000  # look at up to 3h of data

    if names is None:
        names = dict()

    damage = []

    next_start = start

    print("Fetching damage-taken events from WCL...")
    progress_bar = ProgressBar(end - start, length=70)

    # will have to loop to get results
    request_more = True
    while request_more:
        url = f"{API_ROOT}/report/events/damage-taken/{code}?start={next_start}&end={end}&api_key={API_KEY}"

        print(progress_bar.render(next_start - start), end="\r")

        data = _get_api_request(url)
        events = data["events"]
        if "nextPageTimestamp" in data:
            next_start = data["nextPageTimestamp"]
        else:
            request_more = False

        for e in events:
            try:
                timestamp = e["timestamp"]
                timestamp = datetime.fromtimestamp(timestamp / 1000.0).time()
                # spell_id = str(e["ability"]["guid"])

                # if "sourceID" not in e:
                #     # heal not from a player, skipping
                #     continue

                target_id = e["targetID"]
                target = names.get(target_id, f"[pid {target_id}]")

                if for_player and target != for_player:
                    continue

                source_id = e.get("sourceID", None)

                if source_id is None:
                    source = None
                else:
                    source = names.get(source_id, f"[pid {source_id}]")

                # target = names.get(target, f"[pid {target}]")
                health_pct = e.get("hitPoints", None)
                # event_type = e["type"]

                amount = e["amount"]
                mitigated = e.get("mitigated", 0)
                overkill = e.get("overkill", -1)

                # is_crit = e.get("hitType", 1) == 2

                if amount == 0:
                    # ignore attacks that do no damage
                    continue

                event = DamageTakenEvent(
                    timestamp,
                    source,
                    source_id,
                    0,
                    target,
                    target_id,
                    health_pct,
                    -(amount + mitigated),
                    -mitigated,
                    -overkill,
                )
                damage.append(event)
            except Exception as ex:
                print("Exception while handling line", e)
                print(ex)

    print(progress_bar.render(end - start))

    return damage


def get_heals(code, start=None, end=None, character_name=None, **_):
    """
    Gets heal events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    names = get_player_names(code)

    if start is None:
        start = 0

    if end is None:
        fight_data = get_fights(code)
        end = fight_data["end"] - fight_data["start"]

    return _get_heals(code, start, end, names, for_player=character_name)


def get_damage(code, start=None, end=None, character_name=None, **_):
    """
    Gets damage-taken events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    names = get_player_names(code)

    if start is None:
        start = 0

    if end is None:
        fight_data = get_fights(code)
        end = fight_data["end"] - fight_data["start"]

    return _get_damage(code, start, end, names, for_player=character_name)


def get_heals_and_damage(code, start=None, end=None, character_name=None, **_):
    """
    Gets heal and damage-taken events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    names = get_player_names(code)

    if start is None:
        start = 0

    if end is None:
        fight_data = get_fights(code)
        end = fight_data["end"] - fight_data["start"]

    damage = _get_damage(code, start, end, names, for_player=character_name)
    heals, periodics, _ = _get_heals(code, start, end, names, for_player=character_name)

    # join damage, heals, periodics and sort by timestamp
    return sorted(damage + heals + periodics, key=lambda e: e[0])


def _test_code():
    import argparse

    parser = argparse.ArgumentParser("Tests the api reading code.")

    parser.add_argument("code")
    parser.add_argument("-n", "--name")

    args = parser.parse_args()

    # heals, periodics, absorbs = get_heals(args.code, character_name=args.name)
    # print("Heals")
    # for h in heals[:20]:
    #     print("  ", *h)
    #
    # print("Periodics")
    # for h in periodics[:20]:
    #     print("  ", *h)
    #
    # print("Absorbs")
    # for h in absorbs[:20]:
    #     print("  ", *h)

    # damage = get_damage(args.code, character_name=args.name)
    # print("Damage")
    # for e in damage:
    #     print("  ", *e)

    all_events = get_heals_and_damage(args.code, character_name=args.name)
    print("All events")
    for e in all_events[:50]:
        print("  ", *e)


if __name__ == "__main__":
    _test_code()
