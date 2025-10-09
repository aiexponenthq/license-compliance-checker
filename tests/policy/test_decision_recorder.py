from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lcc.config import LCCConfig
from lcc.models import Component, ComponentFinding, ComponentType
from lcc.policy.decision_recorder import DecisionRecorder


class DecisionRecorderTests(unittest.TestCase):
    def test_records_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = LCCConfig()
            config.decision_log_path = Path(tmp_dir) / "decisions.jsonl"
            recorder = DecisionRecorder(config)

            component = Component(type=ComponentType.PYTHON, name="demo", version="1.0.0")
            finding = ComponentFinding(component=component, resolved_license="MIT", confidence=0.9)
            decision = {"status": "pass", "reason": "allowed"}

            recorder.record(finding, decision)

            contents = config.decision_log_path.read_text(encoding="utf-8").strip()
            entry = json.loads(contents)
            self.assertEqual(entry["component"]["name"], "demo")
            self.assertEqual(entry["decision"], decision)


if __name__ == "__main__":
    unittest.main()
