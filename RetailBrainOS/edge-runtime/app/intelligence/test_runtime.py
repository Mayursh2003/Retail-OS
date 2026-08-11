from __future__ import annotations

import time

from app.intelligence.retail_vision_runtime import (
    RetailVisionRuntime,
)


def main() -> None:

    runtime = RetailVisionRuntime()

    print()
    print("=" * 60)
    print("Retail Vision Runtime Test")
    print("=" * 60)
    print()

    runtime.start()

    print("Runtime started.")
    print("Press Ctrl+C to stop.")
    print()

    try:

        while runtime.is_running():

            state = runtime.get_state()

            print(
                f"\r"
                f"Frame: {state.frame_number} | "
                f"FPS: {state.fps:.1f} | "
                f"Processing: "
                f"{state.processing_ms:.1f} ms | "
                f"Zones: {len(state.zones)}",
                end="",
                flush=True,
            )

            time.sleep(0.5)

    except KeyboardInterrupt:

        print()
        print()
        print("Stopping...")

    finally:

        runtime.stop()

    print("Runtime stopped.")


if __name__ == "__main__":
    main()