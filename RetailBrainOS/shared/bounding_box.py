from pydantic import BaseModel, ConfigDict


class BoundingBox(BaseModel):
    """
    Represents the location of a detected person in a frame.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    width: float
    height: float