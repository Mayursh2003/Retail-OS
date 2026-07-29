class StreamError(Exception):
    """
    Base exception for stream-related errors.
    """


class StreamConnectionError(StreamError):
    """
    Raised when an invalid stream connection state transition occurs.
    """


class StreamNotFoundError(StreamError):
    """
    Raised when a requested stream cannot be found.
    """