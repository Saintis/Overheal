"""
Readers module, collection of code to handle reading in the data for analysis.

By: Filip Gokstorp (Saintis), 2020
"""

import readers.read_from_api as api
import readers.read_from_raw as raw


def read_heals(player_name, source, **kwargs):
    """
    Read data from specified source
    """

    if "https://" in source or "http://" in source:
        # https://classic.warcraftlogs.com/reports/RmAaFJB2p1VrDHLT#fight=27&type=healing
        code = source.split("#")[0].split("/")[-1]
        # use a link to a WCL report instead
        heals, periodics, absorbs = api.get_heals(code, name=player_name, **kwargs)
    elif ".txt" in source:
        log_lines = raw.get_lines(source)
        heals, periodics = raw.get_heals(player_name, log_lines)
        absorbs = []
    else:
        # Try assuming source is just the code
        code = source
        heals, periodics, absorbs = api.get_heals(code, name=player_name, **kwargs)

    return heals, periodics, absorbs