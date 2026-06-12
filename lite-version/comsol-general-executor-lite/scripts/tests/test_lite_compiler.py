from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from api_cache import load_api_cache
from compact_task import compile_task, load_task
from lint_plan import lint_plan


class LiteCompilerTests(unittest.TestCase):
    def load_template(self, name: str) -> dict:
        return load_task(ROOT / "assets" / "templates" / name)

    def test_cache_has_provenance_and_exact_version(self):
        cache = load_api_cache("6.4")
        self.assertEqual(cache["comsol_version"], "6.4")
        self.assertTrue(cache["verified_on"])
        self.assertTrue(cache["verification_scope"])

    def test_cache_miss_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            load_api_cache("99.9")

    def test_layer_stack_compiles_and_lints(self):
        task = self.load_template("lite-layer-stack-ewfd.json")
        manifest = compile_task(task)
        component = manifest["components"][0]
        self.assertEqual(len(component["geometry"]["features"]), 19)
        self.assertEqual(manifest["verification"]["expected_stored_points"], 351)
        self.assertEqual(manifest["parameters"]["Lx"], "3940[nm]")
        self.assertEqual(lint_plan(manifest), [])

    def test_diffusion_compiles_and_lints(self):
        task = self.load_template("lite-diffusion-1d.json")
        manifest = compile_task(task)
        self.assertEqual(manifest["verification"]["expected_stored_points"], 21)
        self.assertTrue(manifest["verification"]["require_baseline_comparison"])
        self.assertEqual(lint_plan(manifest), [])

    def test_compact_layer_task_is_smaller_than_expanded_manifest(self):
        task_path = ROOT / "assets" / "templates" / "lite-layer-stack-ewfd.json"
        task = load_task(task_path)
        manifest = compile_task(task)
        task_bytes = len(json.dumps(task, separators=(",", ":")).encode("utf-8"))
        manifest_bytes = len(
            json.dumps(manifest, separators=(",", ":")).encode("utf-8")
        )
        self.assertLess(task_bytes / manifest_bytes, 0.35)

    def test_feature_graph_preserves_generic_manifest(self):
        task = {
            "schema": "comsol-lite-task-v1",
            "template": "feature-graph",
            "id": "generic",
            "comsol_version": "6.4",
            "manifest": {
                "components": [],
                "studies": [],
                "save_policy": {"solved_file": "project/generic.mph"},
            },
        }
        manifest = compile_task(task)
        self.assertEqual(manifest["simulation_id"], "generic")
        self.assertEqual(manifest["comsol_version"], "6.4")

    def test_unknown_profile_fails_closed(self):
        task = {
            "schema": "comsol-lite-task-v1",
            "template": "feature-graph",
            "id": "bad-profile",
            "comsol_version": "6.4",
            "manifest": {
                "components": [
                    {
                        "physics": [
                            {
                                "tag": "p",
                                "profile": "comsol64.not-verified",
                            }
                        ]
                    }
                ],
                "studies": [],
                "save_policy": {"solved_file": "project/bad.mph"},
            },
        }
        with self.assertRaisesRegex(ValueError, "Unverified"):
            compile_task(task)

    def test_output_dir_cannot_escape_workspace(self):
        task = self.load_template("lite-diffusion-1d.json")
        task["output_dir"] = "../outside"
        with self.assertRaisesRegex(ValueError, "parent segments"):
            compile_task(task)

    def test_lite_run_compile_failure_is_one_json_line(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_path = root / "bad-task.json"
            config_path = root / "config.json"
            task_path.write_text(
                json.dumps(
                    {
                        "schema": "comsol-lite-task-v1",
                        "template": "diffusion-1d",
                        "id": "bad",
                        "comsol_version": "99.9",
                        "time_range": {"start": 0, "step": 1, "stop": 2},
                    }
                ),
                encoding="utf-8",
            )
            config_path.write_text(
                json.dumps({"workspace_root": str(root)}), encoding="utf-8"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "lite_run.py"),
                    "--task",
                    str(task_path),
                    "--config",
                    str(config_path),
                    "--timeout-seconds",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            lines = result.stdout.strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["gate"], "setup_or_compile")
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
