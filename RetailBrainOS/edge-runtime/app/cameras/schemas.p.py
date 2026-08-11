from enum import Enum


class CameraStatus(str, Enum):
    """
    Supported camera lifecycle states.
    """

    REGISTERED = "registered"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"