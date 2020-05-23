"""
Read data from WCL API.

By: Filip Gokstorp (Saintis), 2020
"""
import requests
from json.decoder import JSONDecodeError
from datetime import datetime

try:
    API_KEY = open("apikey.txt").read().strip()
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
        print("Error getting an API request:")
        print(req.text)
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

    print("Fetching data from WCL...")
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

                source = e["sourceID"]
                source = names.get(source, f"[pid {source}]")

                if for_player and source != for_player:
                    continue

                target = e["targetID"]
                target = names.get(target, f"[pid {source}]")
                # event_type = e["type"]

                amount = e["amount"]

                if e["type"] == "absorbed":
                    # Shield absorb
                    absorbs.append((timestamp, source, spell_id, target, amount, 0, False))
                    continue

                overheal = e.get("overheal", 0)

                if e.get("tick"):
                    # Periodic tick
                    periodics.append(
                        (timestamp, source, spell_id, target, amount + overheal, overheal, False)
                    )
                    continue

                is_crit = e.get("hitType", 1) == 2

                heals.append(
                    (
                        timestamp,
                        source,
                        spell_id,
                        target,
                        amount + overheal,
                        overheal,
                        is_crit,
                    )
                )
            except Exception as ex:
                print("Exception while handling line", e)
                print(ex)

    print(progress_bar.render(end))

    return heals, periodics, absorbs


def get_heals(code, start=None, end=None, name=None, **_):
    """
    Gets heal events for specified log code.

    :param code: the WarcraftLogs code.
    :param start: the start time, in milliseconds, to get heals for.
    :param end: the end time, in milliseconds, to get heals for. If None, gets logs for up to 3 hours.
    :param name: Optional. Name to filter heal events for.

    :returns (heals, periodic_heals, absorbs), lists of heal events
    """
    names = get_player_names(code)

    if start is None:
        start = 0

    if end is None:
        fight_data = get_fights(code)
        end = fight_data["end"] - fight_data["start"]

    return _get_heals(code, start, end, names, for_player=name)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Tests the api reading code.")

    parser.add_argument("code")
    parser.add_argument("-n", "--name")

    args = parser.parse_args()
    heals, periodics, absorbs = get_heals(args.code, name=args.name)

    print("Heals")
    for h in heals[:20]:
        print("  ", *h)

    print("Periodics")
    for h in periodics[:20]:
        print("  ", *h)

    print("Absorbs")
    for h in absorbs[:20]:
        print("  ", *h)
