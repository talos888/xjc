#!/usr/bin/env python
"""Export solved COMSOL results into a lightweight reusable data package.

This script intentionally does not build, modify, solve, or save COMSOL models.
It is a file handoff endpoint: a modeling workflow leaves a solved .mph file and
this script dehydrates selected results into CSV/NPZ data plus manifest metadata
for later Python analysis without reopening COMSOL.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import sys
import traceback
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Series:
    name: str
    x: list[float]
    y: list[float]
    unit: str = ""
    source: str = ""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def normalize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Accept a small set of obvious aliases while keeping one internal schema."""
    normalized = dict(spec)
    if "project_root" not in normalized and "workspace_root" in normalized:
        normalized["project_root"] = normalized["workspace_root"]

    exports = normalized.get("exports")
    if isinstance(exports, dict):
        normalized.setdefault("plot_groups", exports.get("plot_groups", []))
        normalized["exports"] = exports.get("expressions", [])

    analysis = normalized.get("analysis")
    if isinstance(analysis, dict):
        normalized.setdefault("x_axis", analysis.get("x_axis"))
        if analysis.get("python_plots"):
            normalized["series_plots"] = analysis["python_plots"]
        else:
            normalized.setdefault("series_plots", analysis.get("series_plots", []))

    fixed_expressions = []
    raw_exports = normalized.get("exports", normalized.get("expressions", []))
    for item in raw_exports:
        fixed = dict(item)
        if "expr" not in fixed and "expression" in fixed:
            fixed["expr"] = fixed["expression"]
        fixed.setdefault("format", "csv")
        fixed_expressions.append(fixed)
    normalized["exports"] = fixed_expressions

    axis = normalized.get("x_axis")
    if isinstance(axis, dict) and "type" not in axis and "mode" in axis:
        axis = dict(axis)
        axis["type"] = axis["mode"]
        normalized["x_axis"] = axis
    return normalized


def resolve_path(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = base / p
    return p.resolve()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def linear_axis(start: float, step: float, count: int) -> list[float]:
    return [start + step * i for i in range(count)]


def coerce_float(value: Any, complex_mode: str = "magnitude") -> float:
    if isinstance(value, complex):
        if complex_mode == "real":
            return float(value.real)
        if complex_mode == "imag":
            return float(value.imag)
        if complex_mode == "phase":
            return float(math.atan2(value.imag, value.real))
        return float(abs(value))
    try:
        c = complex(value)
    except Exception:
        return float(value)
    if abs(c.imag) < 1e-14:
        return float(c.real)
    return coerce_float(c, complex_mode)


def flatten_numeric(values: Any, complex_mode: str = "magnitude") -> list[float]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        return [coerce_float(values, complex_mode)]
    if isinstance(values, Iterable):
        out: list[float] = []
        for item in values:
            if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
                out.extend(flatten_numeric(item, complex_mode))
            else:
                out.append(coerce_float(item, complex_mode))
        return out
    return [coerce_float(values, complex_mode)]


def summarize_series(series: Series) -> dict[str, Any]:
    y = series.y
    if not y:
        return {
            "name": series.name,
            "count": 0,
            "unit": series.unit,
            "source": series.source,
            "status": "empty",
        }
    min_i = min(range(len(y)), key=lambda i: y[i])
    max_i = max(range(len(y)), key=lambda i: y[i])
    mean = sum(y) / len(y)
    summary = {
        "name": series.name,
        "count": len(y),
        "min": y[min_i],
        "max": y[max_i],
        "mean": mean,
        "argmin_index": min_i,
        "argmax_index": max_i,
        "unit": series.unit,
        "source": series.source,
    }
    if series.x and len(series.x) == len(y):
        summary["argmin_x"] = series.x[min_i]
        summary["argmax_x"] = series.x[max_i]
        summary["x_start"] = series.x[0]
        summary["x_end"] = series.x[-1]
    return summary


def write_series_csv(path: Path, series: Series) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "x", "y"])
        for i, y in enumerate(series.y):
            x = series.x[i] if series.x and i < len(series.x) else ""
            writer.writerow([i, x, y])


def write_series_npz(path: Path, series: Series) -> None:
    ensure_dir(path.parent)
    import numpy as np  # type: ignore

    np.savez_compressed(
        path,
        name=series.name,
        x=np.asarray(series.x, dtype=float),
        y=np.asarray(series.y, dtype=float),
        unit=series.unit,
        source=series.source,
    )


def read_series_csv(path: Path, name: str | None = None, unit: str = "") -> Series:
    x: list[float] = []
    y: list[float] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            y.append(float(row.get("y") or row.get("value") or row.get("data") or 0.0))
            raw_x = row.get("x")
            if raw_x not in (None, ""):
                x.append(float(raw_x))
    return Series(name=name or path.stem, x=x, y=y, unit=unit, source=str(path))


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md_path(path_value: str) -> str:
    return Path(path_value).as_posix()


def write_svg_plot(path: Path, title: str, series_list: list[Series], x_label: str = "x", y_label: str = "value") -> None:
    ensure_dir(path.parent)
    nonempty = [s for s in series_list if s.y]
    width, height = 900, 520
    margin_l, margin_r, margin_t, margin_b = 80, 30, 55, 70
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]

    if not nonempty:
        content = f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'><text x='20' y='40'>No data</text></svg>"
        path.write_text(content, encoding="utf-8")
        return

    xs: list[float] = []
    ys: list[float] = []
    for s in nonempty:
        sx = s.x if s.x and len(s.x) == len(s.y) else list(range(len(s.y)))
        xs.extend(sx)
        ys.extend(s.y)
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_min -= 0.5
        x_max += 0.5
    if y_min == y_max:
        y_min -= 0.5
        y_max += 0.5
    y_pad = 0.05 * (y_max - y_min)
    y_min -= y_pad
    y_max += y_pad

    def px(x: float) -> float:
        return margin_l + (x - x_min) / (x_max - x_min) * plot_w

    def py(y: float) -> float:
        return margin_t + (y_max - y) / (y_max - y_min) * plot_h

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        f"<text x='{width/2}' y='28' text-anchor='middle' font-family='Arial' font-size='20'>{svg_escape(title)}</text>",
        f"<line x1='{margin_l}' y1='{margin_t + plot_h}' x2='{margin_l + plot_w}' y2='{margin_t + plot_h}' stroke='#111827'/>",
        f"<line x1='{margin_l}' y1='{margin_t}' x2='{margin_l}' y2='{margin_t + plot_h}' stroke='#111827'/>",
    ]
    for i in range(6):
        tx = x_min + (x_max - x_min) * i / 5
        ty = y_min + (y_max - y_min) * i / 5
        lines.append(f"<line x1='{px(tx):.2f}' y1='{margin_t}' x2='{px(tx):.2f}' y2='{margin_t+plot_h}' stroke='#e5e7eb'/>")
        lines.append(f"<text x='{px(tx):.2f}' y='{margin_t+plot_h+25}' text-anchor='middle' font-family='Arial' font-size='12'>{tx:.4g}</text>")
        lines.append(f"<line x1='{margin_l}' y1='{py(ty):.2f}' x2='{margin_l+plot_w}' y2='{py(ty):.2f}' stroke='#e5e7eb'/>")
        lines.append(f"<text x='{margin_l-10}' y='{py(ty)+4:.2f}' text-anchor='end' font-family='Arial' font-size='12'>{ty:.4g}</text>")
    lines.append(f"<text x='{width/2}' y='{height-18}' text-anchor='middle' font-family='Arial' font-size='14'>{svg_escape(x_label)}</text>")
    lines.append(f"<text transform='translate(22 {height/2}) rotate(-90)' text-anchor='middle' font-family='Arial' font-size='14'>{svg_escape(y_label)}</text>")

    for idx, s in enumerate(nonempty):
        sx = s.x if s.x and len(s.x) == len(s.y) else list(range(len(s.y)))
        points = " ".join(f"{px(x):.2f},{py(y):.2f}" for x, y in zip(sx, s.y))
        color = colors[idx % len(colors)]
        lines.append(f"<polyline points='{points}' fill='none' stroke='{color}' stroke-width='2'/>")
        legend_y = margin_t + 18 + idx * 20
        lines.append(f"<line x1='{width-210}' y1='{legend_y-4}' x2='{width-180}' y2='{legend_y-4}' stroke='{color}' stroke-width='3'/>")
        lines.append(f"<text x='{width-172}' y='{legend_y}' font-family='Arial' font-size='13'>{svg_escape(s.name)}</text>")
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def maybe_start_model(model_path: Path):
    import mph  # type: ignore

    client = mph.start(cores=1)
    model = client.load(str(model_path))
    return client, model


def list_result_feature_tags(model: Any) -> list[str]:
    """Return COMSOL result feature tags.

    COMSOL exposes PlotGroups, datasets, numerical features, and export nodes
    under result-related trees. Keep this name broad; callers may still select
    PlotGroup tags for optional diagnostic image export.
    """
    tags = model.java.result().tags()
    return [str(tags[i]) for i in range(len(tags))]


def model_has_solution(model: Any) -> bool:
    try:
        sols = model.solutions()
        return bool(sols)
    except Exception:
        return False


def export_plot_group(model: Any, tag: str, output_path: Path) -> dict[str, Any]:
    ensure_dir(output_path.parent)
    result = model.java.result()
    export = result.export()
    export_tag = f"img_{tag}"
    try:
        if export_tag in [str(t) for t in export.tags()]:
            export.remove(export_tag)
    except Exception:
        pass
    created_type = None
    errors: list[str] = []
    for export_type in ("Image2D", "Image1D", "Image3D", "Image"):
        try:
            export.create(export_tag, export_type)
            created_type = export_type
            break
        except Exception as exc:
            errors.append(f"{export_type}: {exc}")
    if created_type is None:
        return {"tag": tag, "status": "failed", "error": "; ".join(errors)}
    node = export.get(export_tag)
    try:
        result.get(tag).run()
    except Exception:
        pass
    try:
        node.set("plotgroup", tag)
        node.set("pngfilename", str(output_path))
        node.run()
    except Exception as exc:
        return {"tag": tag, "status": "failed", "export_type": created_type, "error": str(exc)}
    return {
        "tag": tag,
        "status": "ok" if output_path.exists() else "missing",
        "export_type": created_type,
        "path": str(output_path),
        "bytes": output_path.stat().st_size if output_path.exists() else 0,
    }


def evaluate_expression(model: Any, item: dict[str, Any]) -> list[float]:
    kwargs: dict[str, Any] = {}
    if item.get("dataset"):
        kwargs["dataset"] = item["dataset"]
    if item.get("inner") is not None:
        kwargs["inner"] = item["inner"]
    if item.get("outer") is not None:
        kwargs["outer"] = item["outer"]
    raw = model.evaluate(item["expr"], **kwargs)
    return flatten_numeric(raw, item.get("complex_mode", "magnitude"))


def build_axis(axis_spec: dict[str, Any] | None, count: int) -> list[float]:
    if not axis_spec:
        return list(range(count))
    if axis_spec.get("type") == "linear" or axis_spec.get("mode") == "linear":
        return linear_axis(float(axis_spec["start"]), float(axis_spec["step"]), count)
    if axis_spec.get("values"):
        values = [float(v) for v in axis_spec["values"]]
        if len(values) == count:
            return values
    return list(range(count))


def copy_report(report_path: Path, copy_to: Path | None) -> str | None:
    if copy_to is None:
        return None
    ensure_dir(copy_to.parent if copy_to.suffix else copy_to)
    destination = copy_to if copy_to.suffix else copy_to / report_path.name
    shutil.copy2(report_path, destination)
    return str(destination)


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def write_package_files(
    output_dir: Path,
    spec: dict[str, Any],
    model_info: dict[str, Any],
    exported_data: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    plots: list[dict[str, Any]],
    image_results: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, str]:
    ensure_dir(output_dir)
    ensure_dir(output_dir / "analysis")
    ensure_dir(output_dir / "logs")
    handoff_path = spec.get("handoff_manifest")
    handoff_summary = None
    if handoff_path:
        hp = resolve_path(Path(model_info.get("project_root", output_dir)), handoff_path)
        if hp and hp.exists():
            try:
                handoff_summary = load_json(hp)
            except Exception as exc:
                warnings.append(f"Could not read handoff_manifest {hp}: {exc}")

    manifest = {
        "package_schema": "comsol-result-package-v2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "title": spec.get("title", "COMSOL result package"),
        "model": model_info,
        "handoff_manifest": handoff_summary,
        "exports": exported_data,
        "plots": plots,
        "diagnostic_images": image_results,
        "warnings": warnings,
    }
    metadata = {
        "purpose": "lightweight COMSOL result package for Python reuse",
        "does_not_contain": ["geometry rebuild instructions", "solver state guarantee", "physical correctness audit"],
        "cleanup_policy": spec.get("cleanup_policy", {"do_not_delete_mph": True}),
        "can_analyze_without_mph": True,
    }
    manifest_path = output_dir / "manifest.json"
    metadata_path = output_dir / "metadata.json"
    summary_path = output_dir / "analysis" / "summary.json"
    log_path = output_dir / "logs" / "export_log.txt"
    manifest_path.write_text(json.dumps(json_safe(manifest), indent=2, ensure_ascii=False), encoding="utf-8")
    metadata_path.write_text(json.dumps(json_safe(metadata), indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path.write_text(json.dumps(json_safe({"series": summaries, "warnings": warnings}), indent=2, ensure_ascii=False), encoding="utf-8")
    log_lines = ["COMSOL result package export log", f"created_utc={manifest['created_utc']}"]
    log_lines.extend(f"warning: {w}" for w in warnings)
    for item in exported_data:
        log_lines.append(f"export: {item.get('name')} status={item.get('status')} path={item.get('path')}")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return {
        "manifest": str(manifest_path),
        "metadata": str(metadata_path),
        "summary": str(summary_path),
        "log": str(log_path),
    }


def write_report(
    path: Path,
    spec: dict[str, Any],
    model_info: dict[str, Any],
    image_results: list[dict[str, Any]],
    series: list[Series],
    summaries: list[dict[str, Any]],
    plots: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    ensure_dir(path.parent)
    lines: list[str] = []
    lines.append(f"# {spec.get('title', 'COMSOL Export/Analysis Report')}")
    lines.append("")
    lines.append("## Scope")
    lines.append("This report exports and analyzes existing COMSOL results only. It does not build, modify, solve, save, or physically validate the model.")
    lines.append("")
    lines.append("## Inputs")
    lines.append(f"- Model: `{model_info.get('model_path', '')}`")
    lines.append(f"- Output directory: `{path.parent}`")
    lines.append(f"- Solution detected: `{model_info.get('has_solution')}`")
    if model_info.get("result_feature_tags"):
        lines.append(f"- Result feature tags: `{', '.join(model_info['result_feature_tags'])}`")
    lines.append("")
    lines.append("## Exported Images")
    if image_results:
        for item in image_results:
            status = item.get("status")
            p = item.get("path", "")
            lines.append(f"- `{item.get('tag')}`: {status}, {item.get('bytes', 0)} bytes, `{p}`")
            if status == "ok" and p:
                lines.append(f"  ![]({md_path(p)})")
    else:
        lines.append("- No image exports requested or no solution available.")
    lines.append("")
    lines.append("## Data Series")
    if summaries:
        lines.append("| name | count | min | max | mean | argmin x | argmax x |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for s in summaries:
            lines.append(
                "| {name} | {count} | {min} | {max} | {mean} | {argmin_x} | {argmax_x} |".format(
                    name=s.get("name", ""),
                    count=s.get("count", 0),
                    min=f"{s.get('min', ''):.6g}" if "min" in s else "",
                    max=f"{s.get('max', ''):.6g}" if "max" in s else "",
                    mean=f"{s.get('mean', ''):.6g}" if "mean" in s else "",
                    argmin_x=f"{s.get('argmin_x', ''):.6g}" if "argmin_x" in s else "",
                    argmax_x=f"{s.get('argmax_x', ''):.6g}" if "argmax_x" in s else "",
                )
            )
    else:
        lines.append("- No expression data exported.")
    lines.append("")
    lines.append("## Analysis Plots")
    if plots:
        for p in plots:
            lines.append(f"- `{p['name']}`: `{p['path']}`")
            lines.append(f"  ![]({md_path(p['path'])})")
    else:
        lines.append("- No Python analysis plots requested.")
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(spec_path: Path) -> dict[str, Any]:
    spec_path = spec_path.resolve()
    spec = normalize_spec(load_json(spec_path))
    root = resolve_path(spec_path.parent, spec.get("project_root")) or spec_path.parent
    output_dir = ensure_dir(resolve_path(root, spec.get("output_dir")) or (root / "result_package"))
    image_dir = ensure_dir(output_dir / "diagnostic_images")
    data_dir = ensure_dir(output_dir / "data")
    plot_dir = ensure_dir(output_dir / "plots")
    analysis_dir = ensure_dir(output_dir / "analysis")
    logs_dir = ensure_dir(output_dir / "logs")
    report_path = analysis_dir / spec.get("report_name", "summary.md")

    model_path = resolve_path(root, spec.get("model"))
    warnings: list[str] = []
    image_results: list[dict[str, Any]] = []
    series_by_name: dict[str, Series] = {}
    model_info: dict[str, Any] = {
        "model_path": str(model_path) if model_path else "",
        "project_root": str(root),
        "has_solution": False,
        "result_feature_tags": [],
    }
    if not model_path and not spec.get("csv_inputs"):
        warnings.append("No data source provided: specify either model or csv_inputs.")

    client = None
    model = None
    if model_path and model_path.exists() and not spec.get("skip_comsol"):
        try:
            client, model = maybe_start_model(model_path)
            model_info["has_solution"] = model_has_solution(model)
            model_info["result_feature_tags"] = list_result_feature_tags(model)
        except Exception as exc:
            warnings.append(f"Could not load COMSOL model: {exc}")
            warnings.append(traceback.format_exc(limit=3))
    elif model_path and not model_path.exists():
        warnings.append(f"Model path does not exist: {model_path}")

    try:
        exported_data: list[dict[str, Any]] = []
        if model is not None and model_info["has_solution"]:
            requested = spec.get("plot_groups", [])
            if requested == "all":
                requested_tags = model_info["result_feature_tags"]
            else:
                requested_tags = [str(x) for x in requested]
            for tag in requested_tags:
                if tag not in model_info["result_feature_tags"]:
                    image_results.append({"tag": tag, "status": "missing_plotgroup", "bytes": 0})
                    continue
                image_results.append(export_plot_group(model, tag, image_dir / f"{tag}.png"))

            for item in spec.get("exports", []):
                name = item["name"]
                try:
                    values = evaluate_expression(model, item)
                    axis = build_axis(item.get("axis") or spec.get("x_axis"), len(values))
                    s = Series(name=name, x=axis, y=values, unit=item.get("unit", ""), source=item.get("expr", ""))
                    series_by_name[name] = s
                    fmt = str(item.get("format", "csv")).lower()
                    if fmt == "npz":
                        data_path = data_dir / f"{name}.npz"
                        write_series_npz(data_path, s)
                    else:
                        data_path = data_dir / f"{name}.csv"
                        write_series_csv(data_path, s)
                    exported_data.append(
                        {
                            "name": name,
                            "expr": item.get("expr"),
                            "format": fmt,
                            "path": str(data_path),
                            "status": "ok",
                            "count": len(values),
                            "axis": item.get("axis") or spec.get("x_axis"),
                        }
                    )
                except Exception as exc:
                    warnings.append(f"Expression export failed for {name}: {exc}")
                    exported_data.append({"name": name, "expr": item.get("expr"), "status": "failed", "error": str(exc)})
        elif model is not None:
            warnings.append("Loaded model has no solution; skipped COMSOL image/expression export.")

        for item in spec.get("csv_inputs", []):
            csv_path = resolve_path(root, item["path"])
            if csv_path and csv_path.exists():
                s = read_series_csv(csv_path, item.get("name"), item.get("unit", ""))
                series_by_name[s.name] = s
            else:
                warnings.append(f"CSV input not found: {csv_path}")

        summaries = [summarize_series(s) for s in series_by_name.values()]
        plots: list[dict[str, Any]] = []
        for plot_spec in spec.get("series_plots", []):
            names = plot_spec.get("series", [])
            selected = [series_by_name[n] for n in names if n in series_by_name]
            missing = [n for n in names if n not in series_by_name]
            if missing:
                warnings.append(f"Plot {plot_spec.get('name', 'unnamed')} missing series: {', '.join(missing)}")
            if selected:
                out = plot_dir / f"{plot_spec.get('name', 'series_plot')}.svg"
                write_svg_plot(
                    out,
                    plot_spec.get("title", plot_spec.get("name", "Series Plot")),
                    selected,
                    plot_spec.get("x_label", "x"),
                    plot_spec.get("y_label", "value"),
                )
                plots.append({"name": plot_spec.get("name", out.stem), "path": str(out)})

        write_report(report_path, spec, model_info, image_results, list(series_by_name.values()), summaries, plots, warnings)
        package_files = write_package_files(output_dir, spec, model_info, exported_data, summaries, plots, image_results, warnings)

        status = {
            "ok": not any(w.startswith("No data source provided") for w in warnings),
            "spec": str(spec_path),
            "output_dir": str(output_dir),
            "package_files": package_files,
            "summary_markdown": str(report_path),
            "diagnostic_images": image_results,
            "data_exports": exported_data,
            "series": summaries,
            "plots": plots,
            "warnings": warnings,
        }
        (logs_dir / "run_status.json").write_text(json.dumps(json_safe(status), indent=2, ensure_ascii=False), encoding="utf-8")
        return status
    finally:
        if client is not None:
            try:
                client.clear()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Path to export_spec.json")
    args = parser.parse_args(argv)
    status = run(Path(args.spec))
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0 if status.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
