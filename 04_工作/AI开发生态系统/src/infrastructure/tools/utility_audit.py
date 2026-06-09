#!/usr/bin/env python3
"""
Utility Truth Validator - Observer Layer
不参与决策，只验证系统是否"说真话"

核心职责：
① Reward Distribution Integrity - reward 是否偏态/极端/collapse
② Preference Stability Index - same input → variance over time
③ Tradeoff Consistency Matrix - 是否出现循环偏好
"""

import sys
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter
from datetime import datetime

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')

from infrastructure.utility_function import (
    create_utility_system, RewardShaper, PreferenceModel,
    TradeoffEngine, OutcomeType
)


@dataclass
class RewardIntegrityResult:
    is_healthy: bool
    distribution_skew: float
    extreme_ratio: float
    collapse_detected: bool
    issues: List[str]


@dataclass
class PreferenceStabilityResult:
    is_stable: bool
    variance_score: float
    weight_drift_rate: float
    ranking_flip_frequency: float
    issues: List[str]


@dataclass
class TradeoffConsistencyResult:
    is_consistent: bool
    contradiction_count: int
    cycle_detected: bool
    contradiction_pairs: List[Tuple[str, str]]
    issues: List[str]


@dataclass
class UtilityAuditReport:
    timestamp: str
    reward_integrity: RewardIntegrityResult
    preference_stability: PreferenceStabilityResult
    tradeoff_consistency: TradeoffConsistencyResult
    overall_healthy: bool
    severity: str


class RewardDistributionAnalyzer:
    def __init__(self, utility_system):
        self.us = utility_system
        self.reward_history: List[float] = []
        self.outcome_history: List[OutcomeType] = []

    def record(self, utility_score: float, outcome: OutcomeType):
        self.reward_history.append(utility_score)
        self.outcome_history.append(outcome)

    def compute_distribution_skew(self) -> float:
        if len(self.reward_history) < 10:
            return 0.0
        mean = sum(self.reward_history) / len(self.reward_history)
        variance = sum((x - mean) ** 2 for x in self.reward_history) / len(self.reward_history)
        std = math.sqrt(variance) if variance > 0 else 0
        if std == 0:
            return 0.0
        skew = sum((x - mean) ** 3 for x in self.reward_history) / (len(self.reward_history) * std ** 3)
        return max(-1.0, min(1.0, skew))

    def compute_extreme_ratio(self, low=0.2, high=0.8) -> float:
        if not self.reward_history:
            return 0.0
        extremes = sum(1 for r in self.reward_history if r <= low or r >= high)
        return extremes / len(self.reward_history)

    def detect_collapse(self, threshold=0.95) -> bool:
        if len(self.reward_history) < 20:
            return False
        counter = Counter(round(r, 2) for r in self.reward_history)
        most_common_ratio = counter.most_common(1)[0][1] / len(self.reward_history)
        return most_common_ratio > threshold

    def analyze(self) -> RewardIntegrityResult:
        skew = self.compute_distribution_skew()
        extreme_ratio = self.compute_extreme_ratio()
        collapse = self.detect_collapse()
        issues = []
        if abs(skew) > 0.5:
            direction = "high" if skew > 0 else "low"
            issues.append(f"Reward distribution is {direction}-skewed ({skew:.2f})")
        if extreme_ratio > 0.8:
            issues.append(f"Extreme ratio too high ({extreme_ratio:.1%})")
        if collapse:
            issues.append("Reward collapse detected")
        healthy = len(issues) == 0 and not collapse
        return RewardIntegrityResult(
            is_healthy=healthy,
            distribution_skew=skew,
            extreme_ratio=extreme_ratio,
            collapse_detected=collapse,
            issues=issues
        )


class PreferenceStabilityAnalyzer:
    def __init__(self, preference_model: PreferenceModel):
        self.pm = preference_model
        self.preference_snapshots: List[Dict[str, float]] = []
        self.comparison_history: List[Tuple[str, str, str]] = []

    def record_preferences(self):
        prefs = {}
        for key in dir(self.pm):
            if not key.startswith('_') and not callable(getattr(self.pm, key)):
                try:
                    val = getattr(self.pm, key)
                    if isinstance(val, (int, float)):
                        prefs[key] = val
                except:
                    pass
        self.preference_snapshots.append(prefs)

    def record_comparison(self, a: str, b: str, winner: str):
        self.comparison_history.append((a, b, winner))

    def compute_variance_score(self) -> float:
        if len(self.preference_snapshots) < 2:
            return 0.0
        all_keys = set()
        for snap in self.preference_snapshots:
            all_keys.update(snap.keys())
        if not all_keys:
            return 0.0
        total_variance = 0.0
        count = 0
        for key in all_keys:
            values = [snap.get(key, 0.0) for snap in self.preference_snapshots]
            if len(values) < 2:
                continue
            mean = sum(values) / len(values)
            if mean == 0:
                continue
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            normalized_var = variance / (mean ** 2) if mean != 0 else 0
            total_variance += normalized_var
            count += 1
        if count == 0:
            return 0.0
        return min(1.0, total_variance / count)

    def compute_ranking_flip_frequency(self) -> float:
        if len(self.comparison_history) < 10:
            return 0.0
        flips = 0
        comparisons = {}
        for a, b, winner in self.comparison_history:
            pair = tuple(sorted([a, b]))
            if pair not in comparisons:
                comparisons[pair] = winner
            elif comparisons[pair] != winner:
                flips += 1
        return flips / len(self.comparison_history)

    def analyze(self) -> PreferenceStabilityResult:
        variance_score = self.compute_variance_score()
        flip_freq = self.compute_ranking_flip_frequency()
        issues = []
        if variance_score > 0.5:
            issues.append(f"High preference variance ({variance_score:.2f})")
        if flip_freq > 0.3:
            issues.append(f"High ranking flip frequency ({flip_freq:.1%})")
        is_stable = len(issues) == 0
        return PreferenceStabilityResult(
            is_stable=is_stable,
            variance_score=variance_score,
            weight_drift_rate=variance_score * 0.1,
            ranking_flip_frequency=flip_freq,
            issues=issues
        )


class TradeoffConsistencyAnalyzer:
    def __init__(self, tradeoff_engine: TradeoffEngine):
        self.te = tradeoff_engine
        self.comparison_log: List[Dict] = []

    def record_tradeoff(self, option_a: Dict, option_b: Dict, decision: str, context: str = ""):
        self.comparison_log.append({
            'a': option_a,
            'b': option_b,
            'decision': decision,
            'context': context,
            'a_higher': option_a.get('utility', 0) > option_b.get('utility', 0)
        })

    def detect_cycles(self) -> Tuple[bool, List[Tuple[str, str]]]:
        if len(self.comparison_log) < 3:
            return False, []
        edges = set()
        for entry in self.comparison_log:
            if entry['a_higher']:
                a_key = entry['a'].get('name', str(entry['a']))
                b_key = entry['b'].get('name', str(entry['b']))
                edges.add((a_key, b_key))
        contradictions = []
        edges_list = list(edges)
        for i, (a1, b1) in enumerate(edges_list):
            for j, (a2, b2) in enumerate(edges_list):
                if i >= j:
                    continue
                if b1 == a2:
                    for k, (a3, b3) in enumerate(edges_list):
                        if k <= j:
                            continue
                        if b2 == a3 and b3 == a1:
                            contradictions.append((a1, b1))
        return len(contradictions) > 0, contradictions[:5]

    def analyze(self) -> TradeoffConsistencyResult:
        cycle_detected, contradictions = self.detect_cycles()
        issues = []
        if cycle_detected:
            issues.append(f"Preference cycle detected")
        is_consistent = not cycle_detected
        return TradeoffConsistencyResult(
            is_consistent=is_consistent,
            contradiction_count=len(contradictions),
            cycle_detected=cycle_detected,
            contradiction_pairs=contradictions,
            issues=issues
        )


class UtilityAudit:
    def __init__(self):
        self.us = create_utility_system()
        self.reward_analyzer = RewardDistributionAnalyzer(self.us)
        self.preference_analyzer = PreferenceStabilityAnalyzer(self.us.preference_model)
        self.tradeoff_analyzer = TradeoffConsistencyAnalyzer(self.us.tradeoff_engine)
        self.audit_start = datetime.now().isoformat()

    def record_decision(self, utility_score: float, outcome: OutcomeType,
                       preferences: Dict = None, tradeoff: Dict = None):
        self.reward_analyzer.record(utility_score, outcome)
        if preferences:
            self.preference_analyzer.record_preferences()
        if tradeoff:
            self.tradeoff_analyzer.record_tradeoff(
                tradeoff.get('a', {}),
                tradeoff.get('b', {}),
                tradeoff.get('decision', ''),
                tradeoff.get('context', '')
            )

    def run_audit(self) -> UtilityAuditReport:
        reward_result = self.reward_analyzer.analyze()
        preference_result = self.preference_analyzer.analyze()
        tradeoff_result = self.tradeoff_analyzer.analyze()
        all_healthy = (
            reward_result.is_healthy and
            preference_result.is_stable and
            tradeoff_result.is_consistent
        )
        severity = "OK"
        if not all_healthy:
            if reward_result.collapse_detected or tradeoff_result.cycle_detected:
                severity = "CRITICAL"
            else:
                severity = "WARNING"
        return UtilityAuditReport(
            timestamp=self.audit_start,
            reward_integrity=reward_result,
            preference_stability=preference_result,
            tradeoff_consistency=tradeoff_result,
            overall_healthy=all_healthy,
            severity=severity
        )

    def generate_report(self) -> str:
        report = self.run_audit()
        lines = [
            "=" * 60,
            "UTILITY TRUTH VALIDATOR - Audit Report",
            "=" * 60,
            f"Timestamp: {report.timestamp}",
            f"Overall Status: {report.severity}",
            "",
            "【① Reward Distribution Integrity】",
            f"  Healthy: {report.reward_integrity.is_healthy}",
            f"  Skew: {report.reward_integrity.distribution_skew:.3f}",
            f"  Extreme Ratio: {report.reward_integrity.extreme_ratio:.1%}",
            f"  Collapse: {report.reward_integrity.collapse_detected}",
        ]
        if report.reward_integrity.issues:
            for issue in report.reward_integrity.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")
        lines.extend([
            "",
            "【② Preference Stability Index】",
            f"  Stable: {report.preference_stability.is_stable}",
            f"  Variance Score: {report.preference_stability.variance_score:.3f}",
            f"  Ranking Flip: {report.preference_stability.ranking_flip_frequency:.1%}",
        ])
        if report.preference_stability.issues:
            for issue in report.preference_stability.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")
        lines.extend([
            "",
            "【③ Tradeoff Consistency Matrix】",
            f"  Consistent: {report.tradeoff_consistency.is_consistent}",
            f"  Contradictions: {report.tradeoff_consistency.contradiction_count}",
            f"  Cycle Detected: {report.tradeoff_consistency.cycle_detected}",
        ])
        if report.tradeoff_consistency.issues:
            for issue in report.tradeoff_consistency.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")
        lines.extend(["", "=" * 60, f"Final Verdict: {report.severity}", "=" * 60])
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("Utility Truth Validator - Starting Audit")
    print("=" * 60)
    audit = UtilityAudit()
    print("\n[1] Generating test data...")
    import random
    for i in range(50):
        score = random.uniform(0.3, 0.9) if random.random() > 0.1 else random.uniform(0.1, 0.2)
        outcome = random.choice([OutcomeType.SUCCESS, OutcomeType.PARTIAL, OutcomeType.FAILURE])
        audit.record_decision(score, outcome)
    print(f"    Recorded {50} decisions")
    print("\n[2] Running audit...")
    report = audit.run_audit()
    print(f"\n[3] Results:")
    print(f"    Overall: {report.severity}")
    print(f"    Reward Healthy: {report.reward_integrity.is_healthy}")
    print(f"    Preference Stable: {report.preference_stability.is_stable}")
    print(f"    Tradeoff Consistent: {report.tradeoff_consistency.is_consistent}")
    print("\n" + audit.generate_report())
