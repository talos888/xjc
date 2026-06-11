from __future__ import annotations

import copy
import re
from typing import Any


TOKEN_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_.-]*)\}")


def _lookup(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Unknown manifest macro value: {path}")
        value = value[part]
    return value


def _substitute(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            expanded = _substitute(item, context)
            if isinstance(item, dict) and (
                set(item) == {"$for_each"} or set(item) == {"$repeat"}
            ):
                result.extend(expanded)
            else:
                result.append(expanded)
        return result
    if isinstance(value, dict):
        if set(value) == {"$for_each"}:
            spec = value["$for_each"]
            if not isinstance(spec, dict):
                raise ValueError("$for_each must contain a mapping.")
            variable = str(spec.get("as", "item"))
            items = spec.get("items", [])
            template = spec.get("template")
            if not isinstance(items, list) or template is None:
                raise ValueError("$for_each requires list items and a template.")
            return [
                _substitute(copy.deepcopy(template), {**context, variable: item})
                for item in items
            ]
        if set(value) == {"$repeat"}:
            spec = value["$repeat"]
            if not isinstance(spec, dict):
                raise ValueError("$repeat must contain a mapping.")
            count = int(spec.get("count", 0))
            start = int(spec.get("start", 0))
            variable = str(spec.get("as", "i"))
            template = spec.get("template")
            if count < 0 or template is None:
                raise ValueError("$repeat requires a nonnegative count and a template.")
            return [
                _substitute(copy.deepcopy(template), {**context, variable: start + offset})
                for offset in range(count)
            ]
        return {key: _substitute(item, context) for key, item in value.items()}
    if not isinstance(value, str):
        return value

    match = TOKEN_RE.fullmatch(value)
    if match:
        return copy.deepcopy(_lookup(context, match.group(1)))

    def replace(match: re.Match[str]) -> str:
        resolved = _lookup(context, match.group(1))
        if isinstance(resolved, (dict, list)):
            raise ValueError(
                f"Manifest macro {match.group(1)} is structured and cannot be embedded in text."
            )
        return str(resolved)

    return TOKEN_RE.sub(replace, value)


def expand_manifest(plan: dict[str, Any]) -> dict[str, Any]:
    """Expand generic data macros before linting or COMSOL execution."""
    expanded = _substitute(copy.deepcopy(plan), {})
    if not isinstance(expanded, dict):
        raise ValueError("Expanded manifest must be a mapping.")
    return expanded
