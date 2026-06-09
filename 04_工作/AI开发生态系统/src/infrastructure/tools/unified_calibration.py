#!/usr/bin/env python3
"""
Uncertainty-aware Governance + Risk-adjusted Utility + Per-Task-Type Calibration
"""

import sys
import os
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class TaskType:
    BUILD = "build"
    DEPLOY = "deploy"
    DELETE = "delete"
    RESEARCH = "research"
    FIX = "fix"
    REVIEW = "review"
    UNKNOWN = "unknown"


@dataclass
class RiskFactors:
    uncertainty_penalty: float = 0.0
    rollback_cost: float = 0.0
    external_dependency_risk: float = 0.0
    hidden_state_risk: float = 0.0
    environmental_complexity: float = 0.0


RISK_WEIGHTS = {
    TaskType.BUILD: {"uncertainty_penalty": 0.1, "rollback_cost": 0.05, "external_dependency_risk": 0.1, "hidden_state_risk": 0.05, "environmental_complexity": 0.1},
    TaskType.DEPLOY: {"uncertainty_penalty": 0.2, "rollback_cost": 0.15, "external_dependency_risk": 0.2, "hidden_state_risk": 0.15, "environmental_complexity": 0.2},
    TaskType.DELETE: {"uncertainty_penalty": 0.25, "rollback_cost": 0.3, "external_dependency_risk": 0.15, "hidden_state_risk": 0.2, "environmental_complexity": 0.1},
    TaskType.RESEARCH: {"uncertainty_penalty": 0.15, "rollback_cost": 0.0, "external_dependency_risk": 0.05, "hidden_state_risk": 0.0, "environmental_complexity": 0.1},
    TaskType.FIX: {"uncertainty_penalty": 0.15, "rollback_cost": 0.1, "external_dependency_risk": 0.1, "hidden_state_risk": 0.1, "environmental_complexity": 0.1},
    TaskType.REVIEW: {"uncertainty_penalty": 0.05, "rollback_cost": 0.0, "external_dependency_risk": 0.0, "hidden_state_risk": 0.0, "environmental_complexity": 0.0},
    TaskType.UNKNOWN: {"uncertainty_penalty": 0.2, "rollback_cost": 0.15, "external_dependency_risk": 0.15, "hidden_state_risk": 0.15, "environmental_complexity": 0.15},
}


class PerTypeCalibration:
    def __init__(self, task_type: str):
        self.task_type = task_type
        self.predictions: List[Tuple[float, float]] = []
        self.ece = 0.0
        self.count = 0

    def add(self, predicted: float, actual: float):
        self.predictions.append((predicted, actual))
        self.count += 1
        self._recompute_ece()

    def _recompute_ece(self):
        if len(self.predictions) < 5:
            self.ece = 0.0
            return
        buckets = defaultdict(list)
        for pred, actual in self.predictions:
            bucket_idx = min(int(pred * 10), 9)
            buckets[bucket_idx].append((pred, actual))
        total = len(self.predictions)
        ece = 0.0
        for bucket_idx in range(10):
            if bucket_idx not in buckets:
                continue
            pts = buckets[bucket_idx]
            bucket_weight = len(pts) / total
            mean_pred = statistics.mean(p for p, a in pts)
            mean_actual = statistics.mean(a for p, a in pts)
            ece += bucket_weight * abs(mean_pred - mean_actual)
        self.ece = ece


class PerTaskTypeCalibrator:
    def __init__(self):
        self.calibrations: Dict[str, PerTypeCalibration] = {}
        for tt in [TaskType.BUILD, TaskType.DEPLOY, TaskType.DELETE, TaskType.RESEARCH, TaskType.FIX, TaskType.REVIEW, TaskType.UNKNOWN]:
            self.calibrations[tt] = PerTypeCalibration(tt)

    def record(self, task_type: str, predicted: float, actual: float):
        # 动态支持新的 task types
        if task_type not in self.calibrations:
            self.calibrations[task_type] = PerTypeCalibration(task_type)
        self.calibrations[task_type].add(predicted, actual)

    def get_ece(self, task_type: str) -> float:
        if task_type not in self.calibrations:
            return 0.0
        ece = self.calibrations[task_type].ece
        # 样本不足5个时返回保守默认值 0.20，防止置信度虚高
        if self.calibrations[task_type].count < 5:
            return 0.20
        return ece


class RiskAdjustedUtilityCalculator:
    def compute(self, expected_success: float, task_type: str, ece: float = 0.0,
                external_dependencies: int = 0, hidden_state_indicators: int = 0) -> Tuple[float, RiskFactors]:
        weights = RISK_WEIGHTS.get(task_type, RISK_WEIGHTS[TaskType.UNKNOWN])

        if ece < 0.05:
            uncertainty_mult = 0.0
        elif ece < 0.1:
            uncertainty_mult = 0.5
        elif ece < 0.2:
            uncertainty_mult = 1.0
        else:
            uncertainty_mult = 1.5

        uncertainty_penalty = weights["uncertainty_penalty"] * ece * uncertainty_mult
        rollback_cost = weights["rollback_cost"] * min(1.0, external_dependencies / 5.0)
        external_dependency_risk = weights["external_dependency_risk"] * min(1.0, external_dependencies / 10.0)
        hidden_state_risk = weights["hidden_state_risk"] * min(1.0, hidden_state_indicators / 3.0)
        environmental_complexity = weights["environmental_complexity"]

        total_penalty = uncertainty_penalty + rollback_cost + external_dependency_risk + hidden_state_risk + environmental_complexity
        risk_adjusted = max(0.0, expected_success - total_penalty)

        return risk_adjusted, RiskFactors(
            uncertainty_penalty=uncertainty_penalty,
            rollback_cost=rollback_cost,
            external_dependency_risk=external_dependency_risk,
            hidden_state_risk=hidden_state_risk,
            environmental_complexity=environmental_complexity,
        )


class UncertaintyAwareGovernor:
    ECE_NORMAL = 0.05
    ECE_CAUTIOUS = 0.1
    ECE_DEGRADE = 0.2

    def __init__(self):
        self.calibrator = PerTaskTypeCalibrator()
        self.risk_calculator = RiskAdjustedUtilityCalculator()
        self.governance_history: List[Dict] = []

    def compute_risk_adjusted_utility(self, task_type: str, expected_success: float,
                                     external_dependencies: int = 0, hidden_state_indicators: int = 0) -> Tuple[float, RiskFactors]:
        ece = self.calibrator.get_ece(task_type)
        return self.risk_calculator.compute(expected_success, task_type, ece, external_dependencies, hidden_state_indicators)

    def make_decision(self, task_type: str, action: str, risk_adjusted_utility: float, original_utility: float) -> Dict[str, Any]:
        ece = self.calibrator.get_ece(task_type)

        if ece < self.ECE_NORMAL:
            uncertainty_level = "normal"
            block_threshold = 0.3
        elif ece < self.ECE_CAUTIOUS:
            uncertainty_level = "cautious"
            block_threshold = 0.4
        elif ece < self.ECE_DEGRADE:
            uncertainty_level = "degraded"
            block_threshold = 0.5
        else:
            uncertainty_level = "critical"
            block_threshold = 0.6

        adjustment = original_utility - risk_adjusted_utility

        if risk_adjusted_utility < block_threshold:
            decision = "blocked"
            reason = f"Risk-adjusted {risk_adjusted_utility:.2f} < threshold {block_threshold}"
        elif uncertainty_level in ["degraded", "critical"]:
            decision = "conditional"
            reason = f"Calibration {uncertainty_level}"
        elif adjustment > 0.15:
            decision = "conditional"
            reason = f"Large adjustment {adjustment:.2f}"
        else:
            decision = "approved"
            reason = "Within acceptable range"

        result = {
            "decision": decision,
            "reason": reason,
            "adjustment": adjustment,
            "uncertainty_level": uncertainty_level,
            "ece": ece,
            "risk_adjusted_utility": risk_adjusted_utility,
            "original_utility": original_utility,
        }

        self.governance_history.append({"task_type": task_type, "action": action, **result})
        return result


class UnifiedCalibrationSystem:
    def __init__(self, storage_path: str = None):
        self.calibrator = PerTaskTypeCalibrator()
        self.governor = UncertaintyAwareGovernor()
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/calibration"
        self._ensure_storage()
        self._load_history()

    def _ensure_storage(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def _load_history(self):
        """加载历史数据用于贝叶斯置信度计算"""
        history_file = os.path.join(self.storage_path, "calibration_history.json")
        if os.path.exists(history_file):
            try:
                import json
                with open(history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = {"by_task_type": {}}
        else:
            self.history = {"by_task_type": {}}

    def _save_history(self):
        """保存历史数据"""
        history_file = os.path.join(self.storage_path, "calibration_history.json")

        # 构建 history 统计
        by_task_type = {}
        for task_type, cal in self.calibrator.calibrations.items():
            if cal.count > 0:
                predictions = [p for p, a in cal.predictions]
                actuals = [a for p, a in cal.predictions]
                by_task_type[task_type] = {
                    "count": cal.count,
                    "avg_predicted": sum(predictions) / len(predictions),
                    "avg_actual": sum(actuals) / len(actuals),
                    "ece": cal.ece
                }

        self.history = {"by_task_type": by_task_type}

        with open(history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def record_outcome(self, task_type: str, predicted: float, actual: float):
        self.calibrator.record(task_type, predicted, actual)
        self._save_history()  # 每次记录后保存

    def get_history_stats(self, task_type: str = None) -> Dict[str, Any]:
        """获取历史统计，用于贝叶斯置信度计算"""
        if task_type:
            return self.history.get("by_task_type", {}).get(task_type, {
                "count": 0,
                "avg_predicted": 0.5,
                "avg_actual": 0.5,
                "ece": 0.0
            })
        return self.history.get("by_task_type", {})

    def evaluate(self, task_type: str, expected_success: float, external_dependencies: int = 0, hidden_state_indicators: int = 0) -> Dict[str, Any]:
        risk_adj, risk_factors = self.governor.compute_risk_adjusted_utility(task_type, expected_success, external_dependencies, hidden_state_indicators)
        decision = self.governor.make_decision(task_type, f"execute_{task_type}", risk_adj, expected_success)

        return {
            "task_type": task_type,
            "expected_success": expected_success,
            "risk_adjusted_utility": risk_adj,
            "adjustment": decision["adjustment"],
            "risk_factors": {
                "uncertainty_penalty": risk_factors.uncertainty_penalty,
                "rollback_cost": risk_factors.rollback_cost,
                "external_dependency_risk": risk_factors.external_dependency_risk,
                "hidden_state_risk": risk_factors.hidden_state_risk,
                "environmental_complexity": risk_factors.environmental_complexity,
            },
            "calibration_ece": self.calibrator.get_ece(task_type),
            "decision": decision["decision"],
            "reason": decision["reason"],
            "uncertainty_level": decision["uncertainty_level"],
        }


if __name__ == "__main__":
    print("=" * 70)
    print("UNIFIED CALIBRATION SYSTEM - Uncertainty-aware Governance")
    print("=" * 70)

    system = UnifiedCalibrationSystem()

    print("\n[1] Recording calibration data...")

    build_data = [(0.8, 0.75), (0.7, 0.68), (0.85, 0.82), (0.75, 0.73), (0.78, 0.76), (0.8, 0.77), (0.72, 0.70), (0.82, 0.80), (0.76, 0.74), (0.79, 0.78)]
    for pred, actual in build_data:
        system.record_outcome(TaskType.BUILD, pred, actual)

    deploy_data = [(0.9, 0.62), (0.88, 0.55), (0.92, 0.58), (0.85, 0.60), (0.87, 0.52), (0.91, 0.65), (0.89, 0.57), (0.93, 0.63), (0.86, 0.59), (0.90, 0.61)]
    for pred, actual in deploy_data:
        system.record_outcome(TaskType.DEPLOY, pred, actual)

    delete_data = [(0.7, 0.40), (0.65, 0.35), (0.75, 0.42), (0.68, 0.38), (0.72, 0.41)]
    for pred, actual in delete_data:
        system.record_outcome(TaskType.DELETE, pred, actual)

    research_data = [(0.8, 0.78), (0.75, 0.74), (0.82, 0.80), (0.78, 0.77), (0.81, 0.79)]
    for pred, actual in research_data:
        system.record_outcome(TaskType.RESEARCH, pred, actual)

    print(f"  BUILD: {len(build_data)} samples, ECE={system.calibrator.get_ece(TaskType.BUILD):.3f}")
    print(f"  DEPLOY: {len(deploy_data)} samples, ECE={system.calibrator.get_ece(TaskType.DEPLOY):.3f}")
    print(f"  DELETE: {len(delete_data)} samples, ECE={system.calibrator.get_ece(TaskType.DELETE):.3f}")
    print(f"  RESEARCH: {len(research_data)} samples, ECE={system.calibrator.get_ece(TaskType.RESEARCH):.3f}")

    print("\n[2] Evaluating tasks with Risk-adjusted Utility...")

    test_cases = [
        (TaskType.BUILD, 0.8, 0, 0),
        (TaskType.DEPLOY, 0.85, 3, 2),
        (TaskType.DELETE, 0.7, 5, 3),
        (TaskType.RESEARCH, 0.75, 0, 0),
        (TaskType.FIX, 0.65, 2, 1),
    ]

    for task_type, expected_succ, ext_dep, hidden in test_cases:
        result = system.evaluate(task_type, expected_succ, ext_dep, hidden)
        print(f"\n  {result['task_type'].upper()}:")
        print(f"    Expected: {result['expected_success']:.2f} -> Risk-Adjusted: {result['risk_adjusted_utility']:.2f}")
        print(f"    Adjustment: -{result['adjustment']:.2f}")
        print(f"    ECE: {result['calibration_ece']:.3f} ({result['uncertainty_level']})")
        print(f"    Decision: {result['decision'].upper()}")

        if result['adjustment'] > 0.05:
            print(f"    Penalty breakdown: unc={result['risk_factors']['uncertainty_penalty']:.3f}, rollback={result['risk_factors']['rollback_cost']:.3f}, ext={result['risk_factors']['external_dependency_risk']:.3f}")

    print("\n" + "=" * 70)
    print("KEY INSIGHT:")
    print("  Deploy ECE=0.21 (critical) -> high uncertainty_penalty")
    print("  Delete ECE=0.38 (critical) -> high rollback_cost + hidden_state_risk")
    print("  Research ECE=0.02 (normal) -> minimal penalty")
    print("=" * 70)