"""
Read data from WCL API.

By: Filip Gokstorp (Saintis), 2020
"""
from collections import namedtuple
import os
import requests
from json.decoder import JSONDecodeError
from datetime import datetime

from .event_types import HealEvent, DamageTakenEvent
from .processor import AbstractProcessor

from backend import ProgressBar


APIEncounter = namedtuple("APIEncounter", ("boss", "start", "end"))


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


def _get_api_request(url, **params):
    """
    Get an API request and check status code.

    :param url: full url with request details to use.
    """
    req = requests.get(url, params=dict(api_key=API_KEY, **params))

    if not req.status_code == 200:
        print("Error getting API request:", req.url)
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


class APIProcessor(AbstractProcessor):
    """Processes WCL API for data."""

    def __init__(self, source, character_name=None):
        super().__init__(source, character_name)

        self.code = source
        self._player_names = None

    @property
    def player_names(self):
        if self._player_names is None:
            self.get_player_names()

        return self._player_names

    def get_fights(self):
        url = f"{API_ROOT}/report/fights/{self.code}"
        return _get_api_request(url)

    def get_player_names(self):
        fight_data = self.get_fights()

        friendlies = fight_data["friendlies"]
        player_names = dict()

        for f in friendlies:
            player_id = f["id"]
            player_name = f["name"]
            player_names[player_id] = player_name

        self._player_names = player_names

    def get_heals(self, start=None, end=None):
        """Gets all heals for the log"""
        code = self.source
        for_player = self.character_name
        names = self.player_names

        if start is None:
            start = 0

        if end is None:
            fight_data = self.get_fights()
            end = fight_data["end"] - fight_data["start"]

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
            url = f"{API_ROOT}/report/events/healing/{code}"

            print(progress_bar.render(next_start - start), end="\r")

            data = _get_api_request(url, start=next_start, end=end)
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

    def get_damage(self, start=None, end=None):
        """Gets all heals and damage events for the log"""

        if start is None:
            start = 0

        if end is None:
            end = start + 3 * 60 * 60 * 1000  # look at up to 3h of data

        names = self.player_names

        damage = []

        next_start = start

        print("Fetching damage-taken events from WCL...")
        progress_bar = ProgressBar(end - start, length=70)

        # will have to loop to get results
        request_more = True
        while request_more:
            url = f"{API_ROOT}/report/events/damage-taken/{self.code}"

            print(progress_bar.render(next_start - start), end="\r")

            data = _get_api_request(url, start=next_start, end=end)
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

                    if self.character_name and target != self.character_name:
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

    def get_encounters(self):
        fights = self.get_fights()

        encounters = []
        for f in fights:
            if f.boss == 0:
                continue

            encounters.append(APIEncounter(f.name, f.start, f.end))

        return encounters

    def process(self, start=None, end=None):
        damage = self.get_damage(start, end)
        heals, periodics, absorbs = self.get_heals(start, end)

        heals = sorted(heals + periodics + absorbs, key=lambda e: e[0])
        all_events = sorted(damage + heals + periodics + absorbs, key=lambda e: e[0])

        self.damage = damage
        self.heals = heals
        self.all_events = all_events

    def get_deaths(self):
        pass


def get_heals(code, start=None, end=None, character_name=None, **_):
    """
    Gets heal events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    processor = APIProcessor(code, character_name=character_name)

    return processor.get_heals(start=start, end=end)


def get_damage(code, start=None, end=None, character_name=None, **_):
    """
    Gets damage-taken events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    processor = APIProcessor(code, character_name=character_name)

    return processor.get_damage(start=start, end=end)


def get_heals_and_damage(code, start=None, end=None, character_name=None, **_):
    """
    Gets heal and damage-taken events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param character_name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    processor = APIProcessor(code, character_name=character_name)

    damage = processor.get_damage(start, end)
    heals, periodics, _ = processor.get_heals(start, end)

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
