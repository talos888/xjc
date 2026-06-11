from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LATIN_RE = re.compile(r"[A-Za-z0-9_]+")
PUNCT_RE = re.compile(r"[^\w\s\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_metrics(text: str) -> dict[str, int]:
    cjk = len(CJK_RE.findall(text))
    latin = sum(math.ceil(len(value) / 4) for value in LATIN_RE.findall(text))
    punctuation = len(PUNCT_RE.findall(text))
    return {
        "utf8_bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "lines": text.count("\n") + 1,
        "token_proxy": cjk + latin + punctuation,
    }


def audit_file(path: Path, category: str) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path.resolve()),
        "category": category,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    try:
        item.update(text_metrics(path.read_text(encoding="utf-8")))
        item["text"] = True
    except (UnicodeDecodeError, OSError):
        item["text"] = False
    return item


def resolve_root(spec_path: Path, root_value: str | Path | None) -> Path:
    root = Path(root_value or ".")
    if not root.is_absolute():
        root = spec_path.parent / root
    return root.resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    spec_path = Path(args.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    root = resolve_root(spec_path, spec.get("root"))
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    for category, values in (spec.get("files", {}) or {}).items():
        for value in values:
            path = Path(value)
            if not path.is_absolute():
                path = root / path
            if not path.is_file():
                missing.append(str(path))
                continue
            files.append(audit_file(path, str(category)))
    totals: dict[str, dict[str, int]] = {}
    for item in files:
        bucket = totals.setdefault(
            item["category"],
            {"utf8_bytes": 0, "characters": 0, "lines": 0, "token_proxy": 0},
        )
        if item.get("text"):
            for key in bucket:
                bucket[key] += int(item.get(key, 0))
    report = {
        "name": spec.get("name"),
        "spec": str(spec_path),
        "allowed_inputs": spec.get("allowed_inputs", []),
        "files": files,
        "totals": totals,
        "missing": missing,
        "status": "ok" if not missing else "failed",
    }
    output = Path(spec.get("output", root / "experiment_audit.json"))
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}, ensure_ascii=True))
    raise SystemExit(0 if not missing else 1)


if __name__ == "__main__":
    main()
