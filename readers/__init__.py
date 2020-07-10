"""
Readers module, collection of code to handle reading in the data for analysis.

By: Filip Gokstorp (Saintis), 2020
"""


def url_to_code(source):
    """Converts a url to a source"""
    return source.split("#")[0].split("/")[-1]


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

        heals, periodics = raw.get_heals(source, **kwargs)
        absorbs = []
    else:
        # Try assuming source is just the code
        code = source

        import readers.read_from_api as api

        heals, periodics, absorbs = api.get_heals(code, **kwargs)

    return heals, periodics, absorbs


def get_processor(source, **kwargs):
    """
    Get a data processor for the specified source
    """
    if ".txt" in source:
        # Dealing with a raw combatlog text file
        from .read_from_raw import RawProcessor

        return RawProcessor(source, **kwargs)

    # Assuming source is a url pointing towards a WCL report, or the report code itself
    if "https://" in source or "http://" in source:
        source = url_to_code(source)

    from .read_from_api import APIProcessor

    return APIProcessor(source, **kwargs)
