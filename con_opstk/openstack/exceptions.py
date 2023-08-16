# Custom Exceptions
class OpStkAuthenticationError(Exception):
    pass

class MissingOpenstackObject(Exception):
    pass

class UnknownOpenstackHandler(Exception):
    pass

class NoHandlerFound(Exception):
    def __init__(self, *args):
        self.missing_handlers = args
    def __str__(self):
        return f"Client Handler(s) Not Found : [{self.missing_handlers}]"

class UnsupportedObject(Exception):
    pass

class FailureToScrub(Exception):
    pass

class APIServerDefError(Exception):
    def __init__(self, msg, code):
        self.message = msg
        self.http_status = code
    def __str__(self):
        return f"{self.http_status} - {self.message}"