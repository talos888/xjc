from __future__ import annotations

import argparse
import shutil
import unittest
import uuid
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", required=True)
    parser.add_argument("--temp", required=True)
    args = parser.parse_args()

    temp_root = Path(args.temp).resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    import tempfile

    class SandboxTemporaryDirectory:
        def __init__(self, *args, **kwargs):
            self.name = str(temp_root / f"case_{uuid.uuid4().hex}")
            Path(self.name).mkdir(parents=False)

        def __enter__(self):
            return self.name

        def __exit__(self, exc_type, exc, traceback):
            self.cleanup()
            return False

        def cleanup(self) -> None:
            shutil.rmtree(self.name, ignore_errors=True)

    tempfile.TemporaryDirectory = SandboxTemporaryDirectory
    suite = unittest.defaultTestLoader.discover(args.tests, pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
