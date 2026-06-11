from __future__ import annotations

import sys
import time
from contextlib import suppress

import mph

from common import configure_mph, load_config


def main() -> None:
    config = load_config()
    print("python_executable:", sys.executable)
    print("python_version:", sys.version.split()[0])
    print("mph_module:", mph.__file__)
    configure_mph(mph, config)
    print("session_mode:", "stand-alone")

    started = time.perf_counter()
    client = None
    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        print("client_started:", True)
        print("elapsed_seconds:", round(time.perf_counter() - started, 2))
        print("client_version:", getattr(client, "version", "unknown"))
        print("client_standalone:", getattr(client, "standalone", "unknown"))
        modules = client.modules()
        print("module_count:", len(modules))
        print("first_modules:", ", ".join(modules[:8]))
    finally:
        if client is not None:
            with suppress(Exception):
                client.disconnect()
                print("client_disconnected:", True)


if __name__ == "__main__":
    main()
