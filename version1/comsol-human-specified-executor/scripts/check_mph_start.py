from __future__ import annotations

import sys
import time

def main() -> int:
    try:
        import mph
    except ImportError as error:
        print(f"startup_blocked: {type(error).__name__}: {error}")
        return 1

    print("python_executable:", sys.executable)
    print("python_version:", sys.version.split()[0])
    print("mph_module:", mph.__file__)

    mph.option("session", "stand-alone")
    print("session_mode:", "stand-alone")

    started_at = time.perf_counter()
    client = mph.start(cores=1)
    elapsed = time.perf_counter() - started_at

    print("client_started:", True)
    print("elapsed_seconds:", round(elapsed, 2))
    print("client_version:", getattr(client, "version", "unknown"))
    print("client_standalone:", getattr(client, "standalone", "unknown"))

    modules = client.modules()
    print("module_count:", len(modules))
    print("first_modules:", ", ".join(modules[:8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
