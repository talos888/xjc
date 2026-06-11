from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from comsol_api.executor import OfficialPlanExecutor
from comsol_api.profiles import apply_profile
from comsol_api.preprocess import expand_manifest
from comsol_api.utils import set_properties
from comsol_api.wave_optics import boundary_dimension
from comsol_api.verification import collect_results_report
from lint_plan import lint_plan
from run_from_plan import as_array, evaluate_outputs


class FakeFeature:
    def __init__(self):
        self.set_calls = []
        self.index_calls = []
        self.label_value = None

    def set(self, key, value):
        self.set_calls.append((key, value))

    def setIndex(self, key, value, *indexes):
        self.index_calls.append((key, value, *indexes))

    def label(self, value):
        self.label_value = value


class FakeGeometry:
    def __init__(self):
        self.features = {}
        self.ran = False

    def create(self, tag, api_type):
        self.features[tag] = FakeFeature()

    def feature(self, tag):
        return self.features[tag]

    def run(self):
        self.ran = True


class FakeComponent:
    def __init__(self):
        self.geometry = FakeGeometry()

    def geom(self, tag):
        return self.geometry


class FakeJava:
    def __init__(self):
        self.comp = FakeComponent()

    def component(self, tag):
        return self.comp


class FakeModel:
    def __init__(self):
        self.java = FakeJava()


class FakeTags:
    def __init__(self, values):
        self.values = values

    def tags(self):
        return self.values


class FakeResults:
    def tags(self):
        return ["pg1"]

    def table(self):
        return FakeTags(["tbl1"])

    def numerical(self):
        return FakeTags(["gev1"])


class FakeResultsJava:
    def result(self):
        return FakeResults()


class FakeEvaluationModel:
    def evaluate(self, expression, **kwargs):
        values = {
            "u": [1.0, 2.0, 3.0],
            "u_exact": [1.0, 2.0, 3.0],
            "u_bad": [2.0, 3.0, 4.0],
        }
        return values[expression]


class RunnerCoreTests(unittest.TestCase):
    def test_bool_properties_use_on_off(self):
        feature = FakeFeature()
        set_properties(feature, {"enabled": True, "disabled": False})
        self.assertEqual(feature.set_calls, [("enabled", "on"), ("disabled", "off")])

    def test_geometry_consumes_indexed_properties(self):
        model = FakeModel()
        executor = OfficialPlanExecutor(model, {})
        executor._build_geometry(
            "comp1",
            "geom1",
            {
                "features": [
                    {
                        "tag": "r1",
                        "official_name": "Rectangle",
                        "indexed_properties": [
                            {"property": "pos", "index": 0, "value": "1[mm]"}
                        ],
                    }
                ]
            },
        )
        feature = model.java.comp.geometry.feature("r1")
        self.assertEqual(feature.index_calls, [("pos", "1[mm]", 0)])
        self.assertTrue(model.java.comp.geometry.ran)

    def test_boundary_dimension_infers_from_component(self):
        plan = {"components": [{"tag": "comp3", "dimension": 3}]}
        self.assertEqual(boundary_dimension(plan, "comp3", {}), 2)
        self.assertEqual(boundary_dimension(plan, "comp3", {"dimension": 1}), 1)

    def test_lint_rejects_unknown_references(self):
        plan = {
            "simulation_id": "bad_refs",
            "save_policy": {"solved_file": "bad_refs.mph"},
            "components": [
                {
                    "tag": "comp1",
                    "geometry": {
                        "features": [{"tag": "r1", "official_name": "Rectangle"}]
                    },
                    "mesh": {"auto_size": 4},
                    "physics": [],
                }
            ],
            "studies": [{"tag": "std1", "features": []}],
            "solvers": [{"tag": "sol1", "study": "missing", "features": []}],
            "derived_values": [
                {"tag": "gev1", "api_type": "EvalGlobal", "table": "missing"}
            ],
        }
        issues = lint_plan(plan)
        self.assertTrue(any("unknown study" in issue for issue in issues))
        self.assertTrue(any("unknown table" in issue for issue in issues))

    def test_complex_outputs_require_explicit_mode(self):
        with self.assertRaises(ValueError):
            as_array([1 + 2j])
        self.assertEqual(as_array([3 + 4j], "magnitude").tolist(), [5.0])

    def test_ewfd_profile_preserves_v1_constitutive_properties(self):
        spec = apply_profile(
            {
                "profile": "comsol64.ewfd.wave-equation",
                "properties": {"epsilonr": ["6.25", "0", "0", "0", "4.6225", "0", "0", "0", "1"]},
            }
        )
        properties = spec["properties"]
        self.assertEqual(properties["DisplacementFieldModel"], "RelativePermittivity")
        self.assertEqual(properties["mur"], "1")
        self.assertEqual(properties["sigma"], "0[S/m]")
        self.assertEqual(len(properties["epsilonr"]), 9)

    def test_periodic_port_profile_is_explicit(self):
        spec = apply_profile(
            {
                "profile": "comsol64.ewfd.periodic-port",
                "properties": {
                    "PortName": "1",
                    "PortExcitation": "on",
                    "E0": ["0", "1[V/m]", "0"],
                    "n": "1",
                },
            }
        )
        properties = spec["properties"]
        self.assertEqual(properties["Polarization"], "UserDefined")
        self.assertEqual(properties["InputType"], "E")
        self.assertEqual(properties["n_mat"], "UserDefined")
        self.assertEqual(properties["alpha_inc"], "0")

    def test_for_each_expands_nested_data_without_stringifying_lists(self):
        plan = {
            "features": [
                {
                    "$for_each": {
                        "as": "layer",
                        "items": [
                            {"tag": "r1", "pos": ["0", "0"], "size": ["1", "2"]},
                            {"tag": "r2", "pos": ["1", "0"], "size": ["3", "2"]},
                        ],
                        "template": {
                            "tag": "${layer.tag}",
                            "properties": {
                                "pos": "${layer.pos}",
                                "size": "${layer.size}",
                            },
                        },
                    }
                }
            ]
        }
        features = expand_manifest(plan)["features"]
        self.assertEqual([item["tag"] for item in features], ["r1", "r2"])
        self.assertEqual(features[1]["properties"]["size"], ["3", "2"])

    def test_repeat_supports_embedded_scalar_substitution(self):
        plan = {
            "features": [
                {
                    "$repeat": {
                        "as": "index",
                        "start": 1,
                        "count": 3,
                        "template": {"tag": "r${index}", "properties": {"value": "${index}"}},
                    }
                }
            ]
        }
        features = expand_manifest(plan)["features"]
        self.assertEqual([item["tag"] for item in features], ["r1", "r2", "r3"])
        self.assertEqual(features[0]["properties"]["value"], 1)

    def test_macro_rejects_unknown_values(self):
        with self.assertRaisesRegex(ValueError, "Unknown manifest macro value"):
            expand_manifest({"tag": "${missing.value}"})

    def test_results_verification_checks_tables_and_numerical_nodes(self):
        plan = {
            "verification": {
                "required_result_tags": ["pg1"],
                "required_table_tags": ["missing_table"],
                "required_numerical_tags": ["missing_numerical"],
            }
        }
        report, failures = collect_results_report(FakeResultsJava(), plan)
        self.assertEqual(report["table_tags"], ["tbl1"])
        self.assertTrue(any("missing_table" in item for item in failures))
        self.assertTrue(any("missing_numerical" in item for item in failures))

    def test_output_baseline_comparison_passes_and_records_error(self):
        outputs = [
            {
                "name": "exact",
                "expression": "u",
                "reference_expression": "u_exact",
                "comparison_metric": "relative_l2",
                "comparison_lte": 1e-12,
            }
        ]
        result = evaluate_outputs(FakeEvaluationModel(), outputs, Path("."))[0]
        self.assertEqual(result["comparison"]["relative_l2"], 0.0)
        self.assertTrue(result["comparison"]["passed"])
        self.assertEqual(result["comparison"]["limit"], 1e-12)

    def test_output_baseline_comparison_rejects_excess_error(self):
        outputs = [
            {
                "name": "bad",
                "expression": "u_bad",
                "reference_expression": "u_exact",
                "comparison_metric": "max_abs",
                "comparison_lte": 0.5,
            }
        ]
        with self.assertRaisesRegex(RuntimeError, "Baseline comparison failed"):
            evaluate_outputs(FakeEvaluationModel(), outputs, Path("."))


if __name__ == "__main__":
    unittest.main()
