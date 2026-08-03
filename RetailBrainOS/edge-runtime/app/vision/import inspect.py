import inspect
from ultralytics.trackers.byte_tracker import BYTETracker

with open("byte_tracker_update.txt", "w", encoding="utf-8") as f:
    f.write(inspect.getsource(BYTETracker.update))

print("Saved byte_tracker_update.txt")