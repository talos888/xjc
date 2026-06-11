from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from experiment_audit import resolve_root, text_metrics


class ExperimentAuditTests(unittest.TestCase):
    def test_relative_root_is_resolved_from_spec_directory(self):
        spec_path = Path("C:/tmp/case/audit_spec.json")
        self.assertEqual(
            resolve_root(spec_path, "../evidence"),
            Path("C:/tmp/evidence").resolve(),
        )

    def test_token_proxy_is_deterministic_for_mixed_text(self):
        first = text_metrics("模型 alpha_123.")
        second = text_metrics("模型 alpha_123.")
        self.assertEqual(first, second)
        self.assertGreater(first["token_proxy"], 2)

    def test_utf8_bytes_preserve_chinese_cost(self):
        metrics = text_metrics("模型")
        self.assertEqual(metrics["characters"], 2)
        self.assertEqual(metrics["utf8_bytes"], 6)
        self.assertEqual(metrics["token_proxy"], 2)


if __name__ == "__main__":
    unittest.main()
