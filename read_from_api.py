"""Read data from WCL API."""
import requests
from datetime import datetime

try:
    API_KEY = open("apikey.txt").read().strip()
except FileNotFoundError:
    print("API key not found. Please save in a plain text file called `apikey.txt`.")
    exit(100)

API_ROOT = "https://classic.warcraftlogs.com:443/v1"


def get_fights(code):
    url = f"{API_ROOT}/report/fights/{code}?api_key={API_KEY}"
    return requests.get(url).json()


def get_player_names(code):
    fight_data = get_fights(code)

    friendlies = fight_data["friendlies"]
    player_names = dict()

    for f in friendlies:
        player_id = f["id"]
        player_name = f["name"]
        player_names[player_id] = player_name

    return player_names


def get_heals(code, start=0, end=None, names=None):
    """Gets all heals for the log"""

    if end is None:
        end = start + 3 * 60 * 60 * 1000  # look at up to 3h of data

    url = f"{API_ROOT}/report/events/healing/{code}?start={start}&end={end}&api_key={API_KEY}"

    req = requests.get(url)
    data = req.json()
    events = data["events"]

    if names is None:
        names = dict()

    heals = []
    periodics = []
    absorbs = []

    for e in events:
        try:
            timestamp = e["timestamp"]
            timestamp = datetime.fromtimestamp(timestamp / 1000).time()
            spell_id = e["ability"]["guid"]

            source = e["sourceID"]
            source = names.get(source, f"[pid {source}]")
            target = e["targetID"]
            target = names.get(target, f"[pid {source}]")
            # event_type = e["type"]

            amount = int(e["amount"])

            if e["type"] == "absorb":
                # Shield absorb
                absorbs.append((timestamp, source, spell_id, target, amount))
                continue

            overheal = int(e.get("overheal", "0"))

            if e.get("tick") == "True":
                # Periodic tick
                periodics.append(
                    (timestamp, source, spell_id, target, amount + overheal, overheal)
                )

            is_crit = e.get("hitType", "1") == "2"

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
        except:
            print(e)

    return heals, periodics, absorbs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("code", nargs="?", default="ar9nG3bvDpw6HTdq")
    args = parser.parse_args()

    code = args.code

    player_names = get_player_names(code)

    start = 1 * 60 * 60 * 1000
    start = 0
    end = start + 2 * 60 * 1000
    heals, periodics, absorbs = get_heals(code, start, end, names=player_names)

    for e in heals[:50]:
        print(*e)
