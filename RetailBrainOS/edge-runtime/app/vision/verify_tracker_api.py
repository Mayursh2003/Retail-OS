import inspect

import ultralytics
from ultralytics.trackers.byte_tracker import BYTETracker

print("=" * 80)
print("Retail Brain OS - Ultralytics Tracker Verification")
print("=" * 80)

print(f"Ultralytics Version : {ultralytics.__version__}")

print("\nBYTETracker Constructor")
print("-----------------------")
print(inspect.signature(BYTETracker))

print("\nBYTETracker.update()")
print("-----------------------")
print(inspect.signature(BYTETracker.update))

print("\nBYTETracker Source")
print("-----------------------")
print(inspect.getfile(BYTETracker))

print("\nAvailable Public Methods")
print("-----------------------")

for name, member in inspect.getmembers(BYTETracker):
    if inspect.isfunction(member) and not name.startswith("_"):
        try:
            print(f"{name}{inspect.signature(member)}")
        except Exception:
            print(name)