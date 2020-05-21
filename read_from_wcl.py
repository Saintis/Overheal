"""Functions for scraping data from WarcraftLogs."""
from datetime import time

from bs4 import BeautifulSoup
from selenium import webdriver


def read_webpage(url):
    """Load webpage url and get source"""
    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.headless = True
    browser = webdriver.Firefox(options=fireFoxOptions)
    browser.get(url)

    html_text = browser.page_source
    return html_text


def process_row(row):
    """Extract spell information from row"""
    time_stamp = row.td.text
    time_stamp = time.fromisoformat(time_stamp)

    a_parts = row.find_all("a")

    source = a_parts[0].text

    spell = a_parts[1]
    spell_id = spell["href"].split("=")[1]

    target = a_parts[2].text

    heal_part = row.find("span", style="color: #84F8BD")
    if not heal_part:
        return None

    heal = heal_part.text
    crit = ("*" in heal)
    heal = int(heal.strip("+").strip("*"))

    overheal_part = row.find("span", style="color: #ff8")

    if overheal_part:
        overheal = int(overheal_part.text)
    else:
        overheal = 0

    total_heal = heal + overheal

    return (time_stamp, source, spell_id, target, total_heal, overheal, crit)


def process_html(html_text):
    """Process html text, extracting spell casts"""
    soup = BeautifulSoup(html_text, "lxml")

    rows = soup.find_all("tr", role="row")

    data = []
    # skip first row
    for row in rows[1:]:
        r_data = process_row(row)
        if r_data:
            data.append(r_data)

    return data


def read_from_url(url):
    """Read in data from specified url."""
    html_text = read_webpage(url)
    data = process_html(html_text)

    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?", help="The url to read in")

    args = parser.parse_args()
    url = args.url

    if url is None:
        # url = "https://classic.warcraftlogs.com/reports/RyghWDaTArzF7Kn4#fight=23&type=healing&view=events&source=37"
        url = "https://classic.warcraftlogs.com/reports/ar9nG3bvDpw6HTdq#fight=23&view=events&type=healing&source=19"

    data = read_from_url(url)

    for d in data:
        print(*d)
