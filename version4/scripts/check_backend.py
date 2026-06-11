from __future__ import annotations

import sys
from pprint import pprint

import mph


def main() -> None:
    print("python_executable:", sys.executable)
    print("python_version:", sys.version.split()[0])
    print("mph_module:", mph.__file__)
    print("\nbackend:")
    pprint(mph.discovery.backend())


if __name__ == "__main__":
    main()
