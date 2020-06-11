"""
Readers module, collection of code to handle reading in the data for analysis.

By: Filip Gokstorp (Saintis), 2020
"""


def read_heals(source, **kwargs):
    """
    Read data from specified source
    """

    if "https://" in source or "http://" in source:
        code = source.split("#")[0].split("/")[-1]

        import readers.read_from_api as api

        heals, periodics, absorbs = api.get_heals(code, **kwargs)
    elif ".txt" in source:

        import readers.read_from_raw as raw

        log_lines = raw.get_lines(source)
        heals, periodics = raw.get_heals(log_lines, **kwargs)
        absorbs = []
    else:
        # Try assuming source is just the code
        code = source

        import readers.read_from_api as api

        heals, periodics, absorbs = api.get_heals(code, **kwargs)

    return heals, periodics, absorbs
