#!/usr/bin/env python3
"""
Shadow Mode Runner - Phase 1: Scientific Validation
真实运行，但不执行危险操作，只记录
"""

import sys
import uuid
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import defaultdict, Counter

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class TaskType(Enum):
    CREATE = "create"
    FIX = "fix"
    DEPLOY = "deploy"
    REFACTOR = "refactor"
    REVIEW = "review"
    TEST = "test"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ShadowTask:
    task_id: str
    task_type: TaskType
    description: str
    risk_level: RiskLevel
    timestamp: str
    proposed_agent: str
    proposed_path: List[str]
    utility_prediction: float
    governance_decision: str
    would_execute: bool = False


@dataclass
class ShadowDecision:
    decision_type: str
    task_id: str
    timestamp: str
    proposed_action: Any
    reasoning: str
    alternatives: List[Any]
    selected: Any
    confidence: float
    metadata: Dict[str, Any]


class ShadowModeRunner:
    def __init__(self):
        self.tasks: List[ShadowTask] = []
        self.decisions: List[ShadowDecision] = []
        self.risk_patterns: Dict[str, RiskLevel] = {
            "deploy": RiskLevel.HIGH, "delete": RiskLevel.CRITICAL,
            "drop": RiskLevel.CRITICAL, "truncate": RiskLevel.CRITICAL,
            "rm ": RiskLevel.HIGH, "create": RiskLevel.LOW, "fix": RiskLevel.LOW,
            "refactor": RiskLevel.MEDIUM, "test": RiskLevel.SAFE,
            "review": RiskLevel.SAFE, "analyze": RiskLevel.SAFE,
        }
        self.agent_effectiveness: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def classify_task(self, description: str, task_type_str: str = None) -> TaskType:
        desc_lower = description.lower()
        if task_type_str:
            try:
                return TaskType[task_type_str.upper()]
            except:
                pass
        if "create" in desc_lower or "build" in desc_lower:
            return TaskType.CREATE
        if "fix" in desc_lower or "bug" in desc_lower:
            return TaskType.FIX
        if "deploy" in desc_lower:
            return TaskType.DEPLOY
        if "refactor" in desc_lower:
            return TaskType.REFACTOR
        if "review" in desc_lower:
            return TaskType.REVIEW
        if "test" in desc_lower:
            return TaskType.TEST
        return TaskType.UNKNOWN

    def assess_risk(self, description: str, agent: str, path: List[str]) -> RiskLevel:
        desc_lower = description.lower()
        for pattern, level in self.risk_patterns.items():
            if pattern in desc_lower:
                return level
        if any(p in str(path) for p in ["drop", "delete", "rm", "truncate"]):
            return RiskLevel.CRITICAL
        if agent == "deployer" or "deploy" in str(path):
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    def should_execute(self, task: ShadowTask) -> bool:
        if task.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return False
        return True

    def process_task(self, description: str, task_type_str: str = None,
                    proposed_agent: str = None, proposed_path: List[str] = None,
                    utility_prediction: float = None) -> ShadowTask:
        task_id = str(uuid.uuid4())[:12]
        task_type = self.classify_task(description, task_type_str)
        risk = self.assess_risk(description, proposed_agent or "", proposed_path or [])

        task = ShadowTask(
            task_id=task_id, task_type=task_type, description=description,
            risk_level=risk, timestamp=datetime.now().isoformat(),
            proposed_agent=proposed_agent or "unknown",
            proposed_path=proposed_path or [],
            utility_prediction=utility_prediction or 0.0,
            governance_decision="pending"
        )
        task.would_execute = self.should_execute(task)
        self.tasks.append(task)
        return task

    def record_decision(self, decision_type: str, task_id: str, selected: Any,
                       reasoning: str, confidence: float, metadata: Dict = None):
        self.decisions.append(ShadowDecision(
            decision_type=decision_type, task_id=task_id,
            timestamp=datetime.now().isoformat(), proposed_action=selected,
            reasoning=reasoning, alternatives=[], selected=selected,
            confidence=confidence, metadata=metadata or {}
        ))

    def record_outcome(self, task_id: str, actual_outcome: float, success: bool):
        for decision in reversed(self.decisions):
            if decision.decision_type == "utility" and decision.task_id == task_id:
                decision.metadata["actual_outcome"] = actual_outcome
                decision.metadata["success"] = success
                break

    def print_report(self):
        total = len(self.tasks)
        safe = sum(1 for t in self.tasks if t.risk_level in [RiskLevel.SAFE, RiskLevel.LOW])
        dangerous = sum(1 for t in self.tasks if t.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        shadow_only = sum(1 for t in self.tasks if not t.would_execute)

        utility_decisions = [d for d in self.decisions if d.decision_type == "utility"]
        with_actual = [d for d in utility_decisions if "actual_outcome" in d.metadata]
        if with_actual:
            errors = [abs(d.selected - d.metadata["actual_outcome"]) for d in with_actual]
            utility_accuracy = 1.0 - (sum(errors) / len(errors)) if errors else 0.0
        else:
            utility_accuracy = 0.0

        governance_decisions = [d for d in self.decisions if d.decision_type == "governance"]
        blocked = sum(1 for d in governance_decisions if d.selected in ["blocked", "conditional"])

        print("=" * 70)
        print("SHADOW MODE RUNNER REPORT")
        print("=" * 70)
        print(f"Total: {total} | Safe: {safe} | Dangerous: {dangerous} | Shadow Only: {shadow_only}")
        print(f"Utility Accuracy: {utility_accuracy:.1%} | Governance Blocked: {blocked}")
        print("=" * 70)


class DecisionQualityAuditor:
    def audit_routing(self, decisions: List[ShadowDecision]) -> Dict[str, Any]:
        routing = [d for d in decisions if d.decision_type == "routing"]
        if not routing:
            return {}
        agent_selections = [d.selected for d in routing]
        distribution = Counter(agent_selections)
        most_common = distribution.most_common(1)[0]
        return {
            "total": len(routing),
            "distribution": dict(distribution),
            "concentration": most_common[1] / len(routing)
        }

    def audit_utility(self, decisions: List[ShadowDecision]) -> Dict[str, Any]:
        utility = [d for d in decisions if d.decision_type == "utility"]
        with_actual = [d for d in utility if "actual_outcome" in d.metadata]
        if not with_actual:
            return {"predictions": 0}
        deltas = [d.selected - d.metadata["actual_outcome"] for d in with_actual]
        return {
            "predictions": len(with_actual),
            "mean_error": sum(deltas) / len(deltas),
            "mean_abs_error": sum(abs(d) for d in deltas) / len(deltas)
        }

    def audit_governance(self, decisions: List[ShadowDecision]) -> Dict[str, Any]:
        governance = [d for d in decisions if d.decision_type == "governance"]
        if not governance:
            return {}
        approved = sum(1 for d in governance if d.selected == "approved")
        blocked = sum(1 for d in governance if d.selected == "blocked")
        return {"total": len(governance), "approved": approved, "blocked": blocked}


if __name__ == "__main__":
    print("SHADOW MODE - Phase 1: Scientific Validation")
    print("=" * 70)

    runner = ShadowModeRunner()
    auditor = DecisionQualityAuditor()

    scenarios = [
        ("build user authentication module", "CREATE", "planner", ["planner", "coder"], 0.8),
        ("fix login bug", "FIX", "coder", ["coder"], 0.65),
        ("deploy to production", "DEPLOY", "deployer", ["deployer"], 0.7),
        ("refactor database queries", "REFACTOR", "reviewer", ["reviewer", "coder"], 0.6),
        ("review pull request", "REVIEW", "reviewer", ["reviewer"], 0.9),
        ("add unit tests", "TEST", "tester", ["tester"], 0.85),
        ("fix security vulnerability", "FIX", "coder", ["coder", "reviewer"], 0.5),
        ("delete temporary files", "UNKNOWN", "cleanup", ["cleanup"], 0.3),
    ]

    print("\n[1] Processing tasks...")
    for desc, task_type, agent, path, utility in scenarios:
        task = runner.process_task(desc, task_type, agent, path, utility)
        status = "EXECUTE" if task.would_execute else "SHADOW ONLY"
        print(f"  {task.task_id[:8]}: {task.task_type.value} - {task.risk_level.value} - {status}")
        runner.record_decision("routing", task.task_id, agent, "reasoning", 0.8)
        runner.record_decision("utility", task.task_id, utility, "shaped reward", utility)
        runner.record_decision("governance", task.task_id,
                            "approved" if task.would_execute else "blocked",
                            "risk assessment", 1.0 if task.would_execute else 0.0)

    print("\n[2] Recording outcomes...")
    for i, task in enumerate(runner.tasks[:3]):
        outcome = 0.3 + (i * 0.2)
        success = outcome > 0.5
        runner.record_outcome(task.task_id, outcome, success)
        print(f"  {task.task_id[:8]}: outcome={outcome:.2f}, success={success}")

    print("\n[3] Reports:")
    runner.print_report()

    print("\n[4] Decision Quality Audit:")
    r = auditor.audit_routing(runner.decisions)
    u = auditor.audit_utility(runner.decisions)
    g = auditor.audit_governance(runner.decisions)
    print(f"  Routing: {r.get('total', 0)} decisions, concentration {r.get('concentration', 0):.1%}")
    print(f"  Utility: {u.get('predictions', 0)} predictions, error {u.get('mean_abs_error', 0):.3f}")
    print(f"  Governance: {g.get('total', 0)} decisions, approved {g.get('approved', 0)}, blocked {g.get('blocked', 0)}")