"""Policy testing utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from lcc.config import LCCConfig, load_config
from lcc.policy.base import PolicyManager, evaluate_policy


@dataclass
class PolicyTestCase:
    name: str
    license: str
    expected: str  # pass, warning, violation
    description: Optional[str] = None


@dataclass
class PolicyTestSuite:
    name: str
    policy_name: str
    cases: List[PolicyTestCase]


class PolicyTestResult:
    def __init__(self, suite: PolicyTestSuite) -> None:
        self.suite = suite
        self.passed: List[PolicyTestCase] = []
        self.failed: List[tuple[PolicyTestCase, str]] = []

    def record(self, case: PolicyTestCase, status: str) -> None:
        if status == case.expected:
            self.passed.append(case)
        else:
            self.failed.append((case, status))

    @property
    def success(self) -> bool:
        return not self.failed

    def to_dict(self) -> Dict[str, object]:
        return {
            "suite": self.suite.name,
            "policy": self.suite.policy_name,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "cases": [
                {
                    "name": case.name,
                    "expected": case.expected,
                    "actual": actual,
                }
                for case, actual in self.failed
            ],
        }


def load_suite(path: Path) -> PolicyTestSuite:
    data = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else _load_yaml(path)
    cases = [
        PolicyTestCase(
            name=item["name"],
            license=item["license"],
            expected=item.get("expected", "pass"),
            description=item.get("description"),
        )
        for item in data.get("cases", [])
    ]
    return PolicyTestSuite(name=data.get("name", path.stem), policy_name=data["policy"], cases=cases)


def run_suite(suite: PolicyTestSuite, manager: PolicyManager) -> PolicyTestResult:
    policy = manager.load_policy(suite.policy_name)
    result = PolicyTestResult(suite)
    for case in suite.cases:
        decision = evaluate_policy(policy.data, [case.license])
        result.record(case, decision.status)
    return result


def run_all(config: Optional[LCCConfig] = None, suites_dir: Optional[Path] = None) -> List[PolicyTestResult]:
    config = config or load_config()
    manager = PolicyManager(config)
    suites_dir = suites_dir or (Path.home() / ".lcc" / "policy-tests")
    results: List[PolicyTestResult] = []
    if not suites_dir.exists():
        return results
    for path in suites_dir.glob("*.yml") | suites_dir.glob("*.yaml") | suites_dir.glob("*.json"):
        suite = load_suite(path)
        results.append(run_suite(suite, manager))
    return results


def _load_yaml(path: Path) -> Dict[str, object]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency optional
        raise RuntimeError("pyyaml is required to load policy test suites") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
