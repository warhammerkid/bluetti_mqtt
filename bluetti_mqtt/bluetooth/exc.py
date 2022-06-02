class ParseError(Exception):
    pass


"""Used when requesting data from an invalid page/offset"""
class InvalidRequestError(Exception):
    pass


# Triggers a re-connect
class BadConnectionError(Exception):
    pass
