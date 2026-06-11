from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_event(path: Path, stage: str, status: str, **details: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "status": status,
        **details,
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, default=str) + "\n")


def protect_target(target: Path, force: bool = False) -> Path:
    resolved = target.expanduser().resolve()
    if resolved.exists() and not force:
        raise FileExistsError(f"target_exists: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--details", default="{}")
    args = parser.parse_args()
    details = json.loads(args.details)
    append_event(args.log, args.stage, args.status, **details)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
