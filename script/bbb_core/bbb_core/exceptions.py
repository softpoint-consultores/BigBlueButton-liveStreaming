class InvalidFilterError(Exception):
    """Raised when there is an invalid filter"""
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.get('errors', ['Invalid filter error'])
        kwargs.pop("errors", None)
        Exception.__init__(self, *args, **kwargs)

class StreamAlreadyRunningError(Exception):
    """Raised when the yt account is already streaming"""
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.get('errors', ['Invalid filter error'])
        kwargs.pop("errors", None)
        self.id = kwargs.get('id', None)
        kwargs.pop("id", None)
        Exception.__init__(self, *args, **kwargs)

class NotEnoughResourcesError(Exception):
    """Raised when there is not enough resources to launch a streaming"""
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.get('errors', ['Not enough resources error'])
        kwargs.pop("errors", None)
        Exception.__init__(self, *args, **kwargs)
