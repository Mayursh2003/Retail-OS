"""
Retail Brain OS
Zone Engine

Determines zone membership for tracked people using
bounding-box overlap with hysteresis.

Zone behavior:

    Outside → overlap >= 20% → Enter zone

    Inside  → overlap >= 10% → Remain in zone

    Inside  → overlap < 10%  → Exit zone

The separate enter/exit thresholds prevent zone-state
flickering when a person is near a zone boundary.
"""

from __future__ import annotations

from typing import Iterable

from shared.tracked_person import TrackedPerson

from app.intelligence.zones.zone import Zone


# ---------------------------------------------------------
# Zone membership thresholds
# ---------------------------------------------------------

# A person must reach this overlap ratio to ENTER a zone.
ZONE_ENTER_THRESHOLD = 0.20

# Once inside, the person remains inside until their
# overlap drops below this value.
ZONE_EXIT_THRESHOLD = 0.10


class ZoneEngine:
    """
    Determines zone membership for tracked people.

    Uses bounding-box / polygon overlap with hysteresis.

    Enter:
        overlap >= 20%

    Stay:
        overlap >= 10%

    Exit:
        overlap < 10%
    """

    def __init__(
        self,
        zones: Iterable[Zone] | None = None,
    ) -> None:

        self._zones: dict[str, Zone] = {}

        # -------------------------------------------------
        # Current zone state per tracked person.
        #
        # track_id -> zone_id
        # -------------------------------------------------

        self._person_zones: dict[
            str,
            str,
        ] = {}

        if zones is not None:

            for zone in zones:

                self.add_zone(zone)

    # -----------------------------------------------------
    # Zone management
    # -----------------------------------------------------

    def add_zone(
        self,
        zone: Zone,
    ) -> None:
        """Register a zone."""

        self._zones[
            str(zone.zone_id)
        ] = zone

    def remove_zone(
        self,
        zone_id,
    ) -> None:
        """Remove a zone."""

        zone_key = str(
            zone_id
        )

        self._zones.pop(
            zone_key,
            None,
        )

        # Remove stale references to this zone.
        stale_tracks = [
            track_id
            for track_id, current_zone_id
            in self._person_zones.items()
            if current_zone_id == zone_key
        ]

        for track_id in stale_tracks:

            self._person_zones.pop(
                track_id,
                None,
            )

    def list_zones(self) -> list[Zone]:
        """Return all registered zones."""

        return list(
            self._zones.values()
        )

    # -----------------------------------------------------
    # Point lookup
    # -----------------------------------------------------

    def locate_point(
        self,
        point: tuple[float, float],
    ) -> Zone | None:
        """
        Find the zone containing a point.

        This remains available for callers that require
        traditional point-in-polygon behavior.
        """

        x, y = point

        for zone in self._zones.values():

            if self._point_in_polygon(
                x,
                y,
                zone.polygon,
            ):

                return zone

        return None

    # -----------------------------------------------------
    # Person lookup
    # -----------------------------------------------------

    def locate_person(
        self,
        person: TrackedPerson,
    ) -> Zone | None:
        """
        Determine the current zone for a tracked person.

        The person's bounding box is compared against every
        configured zone.

        Hysteresis:

            Person outside:
                overlap >= 20% → ENTER

            Person already inside:
                overlap >= 10% → STAY

            Person already inside:
                overlap < 10% → EXIT
        """

        track_key = str(
            person.track_id
        )

        box = person.bounding_box

        x_min = float(
            box.x_min
        )

        y_min = float(
            box.y_min
        )

        x_max = float(
            box.x_max
        )

        y_max = float(
            box.y_max
        )

        box_width = (
            x_max - x_min
        )

        box_height = (
            y_max - y_min
        )

        # -------------------------------------------------
        # Invalid bounding box
        # -------------------------------------------------

        if (
            box_width <= 0
            or box_height <= 0
        ):

            return self._current_zone(
                track_key
            )

        # -------------------------------------------------
        # Calculate overlap against all zones.
        # -------------------------------------------------

        zone_ratios: dict[
            str,
            float,
        ] = {}

        for zone in self._zones.values():

            ratio = (
                self._bbox_zone_overlap_ratio(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                    polygon=zone.polygon,
                )
            )

            zone_ratios[
                str(zone.zone_id)
            ] = ratio

        # -------------------------------------------------
        # Check whether this person already has a zone.
        # -------------------------------------------------

        current_zone_id = (
            self._person_zones.get(
                track_key
            )
        )

        # -------------------------------------------------
        # Person is already inside a zone.
        # -------------------------------------------------

        if current_zone_id is not None:

            current_ratio = zone_ratios.get(
                current_zone_id,
                0.0,
            )

            # ---------------------------------------------
            # Stay inside the current zone.
            # ---------------------------------------------

            if (
                current_ratio
                >= ZONE_EXIT_THRESHOLD
            ):

                return self._zones.get(
                    current_zone_id
                )

            # ---------------------------------------------
            # Current zone lost.
            #
            # Before declaring Outside, check whether
            # another zone has become the strongest valid
            # candidate.
            # ---------------------------------------------

            best_zone_id = self._best_zone_id(
                zone_ratios
            )

            if (
                best_zone_id is not None
                and best_zone_id
                != current_zone_id
            ):

                best_ratio = zone_ratios[
                    best_zone_id
                ]

                if (
                    best_ratio
                    >= ZONE_ENTER_THRESHOLD
                ):

                    self._person_zones[
                        track_key
                    ] = best_zone_id

                    return self._zones[
                        best_zone_id
                    ]

            # ---------------------------------------------
            # Person has actually left all zones.
            # ---------------------------------------------

            self._person_zones.pop(
                track_key,
                None,
            )

            return None

        # -------------------------------------------------
        # Person is currently outside.
        #
        # Find the strongest zone whose overlap reaches
        # the ENTER threshold.
        # -------------------------------------------------

        best_zone_id = self._best_zone_id(
            zone_ratios
        )

        if best_zone_id is None:

            return None

        best_ratio = zone_ratios[
            best_zone_id
        ]

        if (
            best_ratio
            < ZONE_ENTER_THRESHOLD
        ):

            return None

        # -------------------------------------------------
        # Person entered a zone.
        # -------------------------------------------------

        self._person_zones[
            track_key
        ] = best_zone_id

        return self._zones[
            best_zone_id
        ]

    # -----------------------------------------------------
    # Current zone
    # -----------------------------------------------------

    def _current_zone(
        self,
        track_key: str,
    ) -> Zone | None:
        """
        Return the currently remembered zone for a track.
        """

        zone_id = self._person_zones.get(
            track_key
        )

        if zone_id is None:
            return None

        return self._zones.get(
            zone_id
        )

    # -----------------------------------------------------
    # Best zone
    # -----------------------------------------------------

    @staticmethod
    def _best_zone_id(
        zone_ratios: dict[
            str,
            float,
        ],
    ) -> str | None:
        """
        Return the zone with the highest overlap ratio.
        """

        if not zone_ratios:

            return None

        best_zone_id = max(
            zone_ratios,
            key=zone_ratios.get,
        )

        if (
            zone_ratios[
                best_zone_id
            ]
            <= 0.0
        ):

            return None

        return best_zone_id

    # -----------------------------------------------------
    # Bounding-box / polygon overlap
    # -----------------------------------------------------

    @classmethod
    def _bbox_zone_overlap_ratio(
        cls,
        *,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        polygon: tuple[
            tuple[float, float],
            ...,
        ],
    ) -> float:
        """
        Calculate what percentage of the person's
        bounding-box area overlaps the zone polygon.

        Returns:

            0.0 -> no overlap

            1.0 -> entire bounding box is inside
                   the zone
        """

        if len(polygon) < 3:

            return 0.0

        bbox_area = (
            (x_max - x_min)
            * (y_max - y_min)
        )

        if bbox_area <= 0:

            return 0.0

        clipped_polygon = [
            (
                float(x),
                float(y),
            )
            for x, y in polygon
        ]

        # -------------------------------------------------
        # Clip against left edge.
        # -------------------------------------------------

        clipped_polygon = (
            cls._clip_polygon(
                clipped_polygon,
                lambda point:
                    point[0] >= x_min,
                lambda current, previous:
                    cls._vertical_intersection(
                        current,
                        previous,
                        x_min,
                    ),
            )
        )

        if not clipped_polygon:

            return 0.0

        # -------------------------------------------------
        # Clip against right edge.
        # -------------------------------------------------

        clipped_polygon = (
            cls._clip_polygon(
                clipped_polygon,
                lambda point:
                    point[0] <= x_max,
                lambda current, previous:
                    cls._vertical_intersection(
                        current,
                        previous,
                        x_max,
                    ),
            )
        )

        if not clipped_polygon:

            return 0.0

        # -------------------------------------------------
        # Clip against top edge.
        # -------------------------------------------------

        clipped_polygon = (
            cls._clip_polygon(
                clipped_polygon,
                lambda point:
                    point[1] >= y_min,
                lambda current, previous:
                    cls._horizontal_intersection(
                        current,
                        previous,
                        y_min,
                    ),
            )
        )

        if not clipped_polygon:

            return 0.0

        # -------------------------------------------------
        # Clip against bottom edge.
        # -------------------------------------------------

        clipped_polygon = (
            cls._clip_polygon(
                clipped_polygon,
                lambda point:
                    point[1] <= y_max,
                lambda current, previous:
                    cls._horizontal_intersection(
                        current,
                        previous,
                        y_max,
                    ),
            )
        )

        if not clipped_polygon:

            return 0.0

        intersection_area = (
            cls._polygon_area(
                clipped_polygon
            )
        )

        return max(
            0.0,
            min(
                1.0,
                intersection_area
                / bbox_area,
            ),
        )

    # -----------------------------------------------------
    # Intersection helpers
    # -----------------------------------------------------

    @staticmethod
    def _vertical_intersection(
        current: tuple[
            float,
            float,
        ],
        previous: tuple[
            float,
            float,
        ],
        x_value: float,
    ) -> tuple[
        float,
        float,
    ]:
        """
        Calculate intersection between a polygon edge
        and a vertical clipping boundary.
        """

        current_x, current_y = current
        previous_x, previous_y = previous

        if (
            current_x
            == previous_x
        ):

            return (
                x_value,
                current_y,
            )

        ratio = (
            x_value
            - previous_x
        ) / (
            current_x
            - previous_x
        )

        return (
            x_value,
            previous_y
            + (
                current_y
                - previous_y
            )
            * ratio,
        )

    @staticmethod
    def _horizontal_intersection(
        current: tuple[
            float,
            float,
        ],
        previous: tuple[
            float,
            float,
        ],
        y_value: float,
    ) -> tuple[
        float,
        float,
    ]:
        """
        Calculate intersection between a polygon edge
        and a horizontal clipping boundary.
        """

        current_x, current_y = current
        previous_x, previous_y = previous

        if (
            current_y
            == previous_y
        ):

            return (
                current_x,
                y_value,
            )

        ratio = (
            y_value
            - previous_y
        ) / (
            current_y
            - previous_y
        )

        return (
            previous_x
            + (
                current_x
                - previous_x
            )
            * ratio,
            y_value,
        )

    # -----------------------------------------------------
    # Polygon clipping
    # -----------------------------------------------------

    @staticmethod
    def _clip_polygon(
        polygon: list[
            tuple[
                float,
                float,
            ]
        ],
        inside,
        intersection,
    ) -> list[
        tuple[
            float,
            float,
        ]
    ]:
        """
        Clip a polygon against one boundary using the
        Sutherland-Hodgman algorithm.
        """

        if not polygon:

            return []

        output: list[
            tuple[
                float,
                float,
            ]
        ] = []

        previous = polygon[-1]

        previous_inside = inside(
            previous
        )

        for current in polygon:

            current_inside = inside(
                current
            )

            if current_inside:

                if not previous_inside:

                    output.append(
                        intersection(
                            current,
                            previous,
                        )
                    )

                output.append(
                    current
                )

            elif previous_inside:

                output.append(
                    intersection(
                        current,
                        previous,
                    )
                )

            previous = current

            previous_inside = (
                current_inside
            )

        return output

    # -----------------------------------------------------
    # Polygon area
    # -----------------------------------------------------

    @staticmethod
    def _polygon_area(
        polygon: list[
            tuple[
                float,
                float,
            ]
        ],
    ) -> float:
        """
        Calculate polygon area using the shoelace formula.
        """

        if len(polygon) < 3:

            return 0.0

        area = 0.0

        for index in range(
            len(polygon)
        ):

            x1, y1 = polygon[
                index
            ]

            x2, y2 = polygon[
                (
                    index + 1
                )
                % len(polygon)
            ]

            area += (
                x1 * y2
                - x2 * y1
            )

        return abs(area) / 2.0

    # -----------------------------------------------------
    # Point-in-polygon
    # -----------------------------------------------------

    @staticmethod
    def _point_in_polygon(
        x: float,
        y: float,
        polygon: tuple[
            tuple[float, float],
            ...,
        ],
    ) -> bool:
        """
        Return True when a point lies inside a polygon.
        """

        if len(polygon) < 3:

            return False

        inside = False

        previous_x, previous_y = (
            polygon[-1]
        )

        for current_x, current_y in polygon:

            intersects = (
                (
                    current_y > y
                )
                != (
                    previous_y > y
                )
                and x
                < (
                    (
                        previous_x
                        - current_x
                    )
                    * (
                        y
                        - current_y
                    )
                    / (
                        previous_y
                        - current_y
                    )
                    + current_x
                )
            )

            if intersects:

                inside = not inside

            previous_x = current_x
            previous_y = current_y

        return inside