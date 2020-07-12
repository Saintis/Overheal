"""
Tests for the scripts.

By: Filip Gökstorp (Saintis-Dreadmist), 2020
"""

python = "python3"
log_file = "tests/test_log.txt"
wcl_report = "https://classic.warcraftlogs.com/reports/xtj2mVgQXFp4n9RT"
code = wcl_report.split("/")[-1]
character = "Saintis"


def test_read_from_api():
    from ..src.readers import read_from_api as api

    all_events = api.get_heals_and_damage(code, character_name=character)

    # TODO: get better test for this.
    assert len(all_events) == 345


def test_read_from_raw():
    from ..src.readers import read_from_raw as raw

    all_events = raw.get_heals_and_damage(log_file, character_name=character)

    # TODO: get better test for this.
    assert len(all_events) == 324
