import json
import cv2
import numpy as np
import os
import time


class ZoneManager:

    def __init__(self):

        PROJECT_ROOT = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../.."
            )
        )

        config_path = os.path.join(
            PROJECT_ROOT,
            "configs",
            "zones_config.json"
        )

        with open(config_path, "r") as file:
            self.zones = json.load(file)

        for zone_name in self.zones:
            self.zones[zone_name] = np.array(
                self.zones[zone_name],
                dtype=np.int32
            )

        # Door center reference
        door_polygon = self.zones["entry_exit_zone"]

        self.door_center_y = int(
            np.mean(door_polygon[:, 1])
        )

        # Statistics
        self.entry_count = 0
        self.exit_count = 0
        self.occupancy_count = 0

        # Track states
        self.visitor_states = {}

        # Recent events
        self.recent_events = []

    def draw_zones(self, frame):

        for zone_name, points in self.zones.items():

            cv2.polylines(
                frame,
                [points],
                True,
                (0, 165, 255),
                2
            )

            center = np.mean(points, axis=0).astype(int)

            cv2.putText(
                frame,
                "DOOR GATE",
                tuple(center),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 165, 255),
                2
            )

    def update_visitor_position(
        self,
        track_id,
        center_position
    ):

        center_x, center_y = center_position

        current_side = (
            "inside"
            if center_y > self.door_center_y
            else "outside"
        )

        current_time = time.strftime(
            "%H:%M:%S"
        )

        if track_id not in self.visitor_states:

            self.visitor_states[track_id] = {
                "side": current_side
            }

            return None

        previous_side = (
            self.visitor_states[track_id]["side"]
        )

        event = None

        # ENTRY
        if (
            previous_side == "outside"
            and current_side == "inside"
        ):

            self.entry_count += 1
            self.occupancy_count += 1

            event = {
                "track_id": track_id,
                "event": "ENTRY",
                "time": current_time
            }

        # EXIT
        elif (
            previous_side == "inside"
            and current_side == "outside"
        ):

            self.exit_count += 1

            self.occupancy_count = max(
                0,
                self.occupancy_count - 1
            )

            event = {
                "track_id": track_id,
                "event": "EXIT",
                "time": current_time
            }

        self.visitor_states[track_id]["side"] = current_side

        if event:

            self.recent_events.insert(
                0,
                event
            )

            self.recent_events = (
                self.recent_events[:10]
            )

            print(event)

        return event