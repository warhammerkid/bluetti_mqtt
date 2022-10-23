class ParseError(Exception):
    pass


class InvalidRequestError(Exception):
    """Used when requesting data from an invalid page/offset"""
    pass


# Triggers a re-connect
class BadConnectionError(Exception):
    pass
