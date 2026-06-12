from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from comsol_api.manifest import file_sha256
from existing_model_common import load_mapping, prepare_output_files
from inspect_model import validate_inspect_plan
from modify_from_plan import _preflight_source_and_manifest, validate_modify_plan


class ExistingModelV0Tests(unittest.TestCase):
    def test_file_sha256_is_stable_and_prefixed(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.mph"
            file.write_bytes(b"model")
            first = file_sha256(file)
            second = file_sha256(file)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("sha256:"))

    def test_inspect_requires_correct_operation(self):
        with self.assertRaises(ValueError):
            validate_inspect_plan({"operation": "build", "job_id": "x", "source_model": "x.mph"})

    def test_existing_model_json_plan_has_zero_dependency_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inspect.json"
            path.write_text(json.dumps({"operation": "inspect"}), encoding="utf-8")
            self.assertEqual(load_mapping(path)["operation"], "inspect")

    def test_modify_rejects_non_parameter_operation(self):
        plan = self.valid_modify_plan()
        plan["ops"] = [{"op": "set_property", "name": "x", "expected_old_value": "1", "value": "2"}]
        with self.assertRaises(ValueError):
            validate_modify_plan(plan)

    def test_modify_requires_clear_solution(self):
        plan = self.valid_modify_plan()
        plan["actions"]["clear_solution"] = False
        with self.assertRaises(ValueError):
            validate_modify_plan(plan)

    def test_output_files_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "result"
            output.mkdir()
            (output / "execution_report.json").write_text(json.dumps({}), encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prepare_output_files(root, {"output_dir": str(output)}, "job")

    def test_preflight_rejects_wrong_sha_and_old_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mph"
            source.write_bytes(b"model")
            actual_sha = file_sha256(source)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "source_model": str(source.resolve()),
                        "source_file_sha256": actual_sha,
                        "parameters": {"n": "1"},
                    }
                ),
                encoding="utf-8",
            )
            plan = self.valid_modify_plan()
            plan["source_model"]["file"] = str(source)
            plan["manifest"]["file"] = str(manifest)
            with self.assertRaisesRegex(ValueError, "Source SHA mismatch"):
                _preflight_source_and_manifest(root, plan)
            plan["source_model"]["expected_file_sha256"] = actual_sha
            plan["ops"][0]["expected_old_value"] = "wrong"
            with self.assertRaisesRegex(ValueError, "manifest value mismatch"):
                _preflight_source_and_manifest(root, plan)

    @staticmethod
    def valid_modify_plan():
        return {
            "operation": "modify",
            "capability_level": "safe_v0",
            "job_id": "job",
            "source_model": {"file": "source.mph", "expected_file_sha256": "sha256:x"},
            "manifest": {"file": "manifest.json"},
            "ops": [
                {
                    "op": "set_parameter",
                    "name": "n",
                    "expected_old_value": "1",
                    "value": "2",
                }
            ],
            "actions": {"clear_solution": True, "solve_studies": ["std1"]},
        }


if __name__ == "__main__":
    unittest.main()
