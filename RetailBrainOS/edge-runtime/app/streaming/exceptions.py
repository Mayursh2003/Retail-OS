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


class FrameAcquisitionError(StreamError):
    """
    Raised when a valid frame cannot be acquired from a stream.
    """