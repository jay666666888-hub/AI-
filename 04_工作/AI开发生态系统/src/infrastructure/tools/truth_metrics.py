#!/usr/bin/env python3
"""
Truth Metrics - 真实性校准系统
不参与决策，只验证"预测"与"真实结果"的一致性

核心职责：
① Utility Truth Metrics - 验证 utility prediction 的诚实度
② Routing Truth Metrics - 验证 routing quality
③ Governance Truth Metrics - 验证 governor 的 false positive/negative rate

这是 Scientific Validation Phase 的核心工具
"""

import sys
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import statistics

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


# ==============================================================================
# Utility Truth Metrics
# ==============================================================================

@dataclass
class UtilityPredictionRecord:
    timestamp: str
    task_id: str
    agent_id: str
    expected_utility: float
    utility_inputs: List[float]
    context: Dict[str, Any]


@dataclass
class UtilityOutcomeRecord:
    timestamp: str
    task_id: str
    agent_id: str
    actual_outcome: float
    outcome_type: str


@dataclass
class UtilityDeltaAnalysis:
    task_id: str
    expected: float
    actual: float
    delta: float
    abs_delta: float
    direction: str
    context: Dict[str, Any]


@dataclass
class UtilityTruthMetrics:
    total_predictions: int
    honest_predictions: int
    overestimated: int
    underestimated: int
    mean_delta: float
    median_delta: float
    std_delta: float
    mean_abs_delta: float
    honesty_score: float
    collapse_risk: float
    reward_hack_risk: float
    issues: List[str]


class UtilityTruthValidator:
    def __init__(self, delta_threshold: float = 0.15):
        self.delta_threshold = delta_threshold
        self.predictions: List[UtilityPredictionRecord] = []
        self.outcomes: List[UtilityOutcomeRecord] = []
        self._prediction_index: Dict[Tuple[str, str], UtilityPredictionRecord] = {}

    def record_prediction(self, task_id: str, agent_id: str,
                         expected_utility: float,
                         utility_inputs: List[float] = None,
                         context: Dict[str, Any] = None):
        record = UtilityPredictionRecord(
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            agent_id=agent_id,
            expected_utility=expected_utility,
            utility_inputs=utility_inputs or [],
            context=context or {}
        )
        self.predictions.append(record)
        self._prediction_index[(task_id, agent_id)] = record

    def record_outcome(self, task_id: str, agent_id: str,
                      actual_outcome: float,
                      outcome_type: str = "success"):
        record = UtilityOutcomeRecord(
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            agent_id=agent_id,
            actual_outcome=actual_outcome,
            outcome_type=outcome_type
        )
        self.outcomes.append(record)

    def match_and_analyze(self) -> List[UtilityDeltaAnalysis]:
        analyses = []
        for outcome in self.outcomes:
            key = (outcome.task_id, outcome.agent_id)
            if key in self._prediction_index:
                pred = self._prediction_index[key]
                delta = pred.expected_utility - outcome.actual_outcome
                abs_delta = abs(delta)
                direction = "accurate"
                if abs_delta > self.delta_threshold:
                    direction = "overestimated" if delta > 0 else "underestimated"
                analyses.append(UtilityDeltaAnalysis(
                    task_id=outcome.task_id,
                    expected=pred.expected_utility,
                    actual=outcome.actual_outcome,
                    delta=delta,
                    abs_delta=abs_delta,
                    direction=direction,
                    context=pred.context
                ))
        return analyses

    def compute_truth_metrics(self) -> UtilityTruthMetrics:
        analyses = self.match_and_analyze()
        if not analyses:
            return UtilityTruthMetrics(
                total_predictions=0, honest_predictions=0, overestimated=0,
                underestimated=0, mean_delta=0.0, median_delta=0.0, std_delta=0.0,
                mean_abs_delta=0.0, honesty_score=0.0, collapse_risk=0.0,
                reward_hack_risk=0.0, issues=["No matched prediction-outcome pairs"]
            )

        deltas = [a.delta for a in analyses]
        abs_deltas = [a.abs_delta for a in analyses]
        honest = sum(1 for a in analyses if a.abs_delta <= self.delta_threshold)
        overest = sum(1 for a in analyses if a.direction == "overestimated")
        underest = sum(1 for a in analyses if a.direction == "underestimated")

        mean_delta = statistics.mean(deltas) if deltas else 0.0
        median_delta = statistics.median(deltas) if deltas else 0.0
        std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
        mean_abs_delta = statistics.mean(abs_deltas) if abs_deltas else 0.0
        honesty_score = honest / len(analyses) if analyses else 0.0

        actuals = [a.actual for a in analyses]
        if len(actuals) > 1:
            actual_variance = statistics.variance(actuals)
            collapse_risk = max(0.0, 1.0 - min(1.0, actual_variance * 10))
        else:
            collapse_risk = 0.0

        recent = analyses[-10:] if len(analyses) > 10 else analyses
        overest_rate = sum(1 for a in recent if a.direction == "overestimated") / len(recent) if recent else 0.0
        reward_hack_risk = overest_rate if overest_rate > 0.5 else 0.0

        issues = []
        if honesty_score < 0.6:
            issues.append(f"Low honesty score ({honesty_score:.1%}) - utility predictions unreliable")
        if collapse_risk > 0.7:
            issues.append(f"High collapse risk ({collapse_risk:.1%}) - utility variance collapsing")
        if reward_hack_risk > 0.5:
            issues.append(f"Reward hack risk ({reward_hack_risk:.1%}) - consistent overestimation")

        return UtilityTruthMetrics(
            total_predictions=len(analyses), honest_predictions=honest,
            overestimated=overest, underestimated=underest,
            mean_delta=mean_delta, median_delta=median_delta, std_delta=std_delta,
            mean_abs_delta=mean_abs_delta, honesty_score=honesty_score,
            collapse_risk=collapse_risk, reward_hack_risk=reward_hack_risk, issues=issues
        )


# ==============================================================================
# Routing Truth Metrics
# ==============================================================================

@dataclass
class RoutingDecisionRecord:
    timestamp: str
    task_id: str
    chosen_agent: str
    context: str
    available_agents: List[str]
    reasoning: str


@dataclass
class RoutingQualityMetrics:
    total_routing_decisions: int
    consistent_routing: int
    inconsistent_routing: int
    consistency_rate: float
    optimal_path_rate: float
    unnecessary_hops: int
    agent_selection_entropy: float
    redundancy_score: float
    issues: List[str]


class RoutingTruthValidator:
    def __init__(self):
        self.routing_decisions: List[RoutingDecisionRecord] = []
        self.task_agent_mapping: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.agent_capabilities: Dict[str, Set[str]] = {}

    def record_routing(self, task_id: str, chosen_agent: str,
                      context: str = "", available_agents: List[str] = None, reasoning: str = ""):
        record = RoutingDecisionRecord(
            timestamp=datetime.now().isoformat(), task_id=task_id,
            chosen_agent=chosen_agent, context=context,
            available_agents=available_agents or [], reasoning=reasoning
        )
        self.routing_decisions.append(record)
        self.task_agent_mapping[task_id][chosen_agent] += 1

    def register_agent_capability(self, agent_id: str, capabilities: List[str]):
        self.agent_capabilities[agent_id] = set(capabilities)

    def compute_quality_metrics(self) -> RoutingQualityMetrics:
        if not self.routing_decisions:
            return RoutingQualityMetrics(
                total_routing_decisions=0, consistent_routing=0, inconsistent_routing=0,
                consistency_rate=0.0, optimal_path_rate=0.0, unnecessary_hops=0,
                agent_selection_entropy=0.0, redundancy_score=0.0,
                issues=["No routing decisions recorded"]
            )

        total = len(self.routing_decisions)
        consistent = sum(sum(counts.values()) for counts in self.task_agent_mapping.values() if len(counts) == 1)
        consistency_rate = consistent / total if total > 0 else 0.0

        agent_counts = Counter(r.chosen_agent for r in self.routing_decisions)
        total_decisions = len(self.routing_decisions)
        entropy = 0.0
        for agent, count in agent_counts.items():
            p = count / total_decisions
            if p > 0:
                entropy -= p * (p ** 0.5)
        agent_selection_entropy = min(1.0, entropy)

        redundancy_score = 0.0
        if len(self.agent_capabilities) > 1:
            agents = list(self.agent_capabilities.keys())
            total_overlap = 0.0
            pair_count = 0
            for i, a in enumerate(agents):
                for j, b in enumerate(agents):
                    if i >= j:
                        continue
                    a_caps = self.agent_capabilities[a]
                    b_caps = self.agent_capabilities[b]
                    intersection = len(a_caps & b_caps)
                    union = len(a_caps | b_caps)
                    if union > 0:
                        total_overlap += intersection / union
                        pair_count += 1
            redundancy_score = total_overlap / pair_count if pair_count > 0 else 0.0

        issues = []
        if consistency_rate < 0.7:
            issues.append(f"Low routing consistency ({consistency_rate:.1%}) - oscillating between agents")
        if redundancy_score > 0.7:
            issues.append(f"High agent redundancy ({redundancy_score:.1%}) - unnecessary duplication")

        return RoutingQualityMetrics(
            total_routing_decisions=total, consistent_routing=consistent,
            inconsistent_routing=total - consistent, consistency_rate=consistency_rate,
            optimal_path_rate=0.0, unnecessary_hops=0, agent_selection_entropy=agent_selection_entropy,
            redundancy_score=redundancy_score, issues=issues
        )


# ==============================================================================
# Governance Truth Metrics
# ==============================================================================

@dataclass
class GovernanceDecisionRecord:
    timestamp: str
    task_id: str
    proposed_action: str
    decision: str
    constraints_checked: List[str]
    reason: str
    actual_outcome: Optional[str] = None


@dataclass
class GovernanceTruthMetrics:
    total_decisions: int
    approvals: int
    blocks: int
    conditionals: int
    fallbacks: int
    false_positive_rate: float
    false_negative_rate: float
    over_conservative_rate: float
    under_conservative_rate: float
    accuracy: float
    issues: List[str]


class GovernanceTruthValidator:
    def __init__(self):
        self.decisions: List[GovernanceDecisionRecord] = []

    def record_decision(self, task_id: str, proposed_action: str, decision: str,
                       constraints_checked: List[str], reason: str, actual_outcome: str = None):
        record = GovernanceDecisionRecord(
            timestamp=datetime.now().isoformat(), task_id=task_id,
            proposed_action=proposed_action, decision=decision,
            constraints_checked=constraints_checked, reason=reason,
            actual_outcome=actual_outcome
        )
        self.decisions.append(record)

    def record_outcome(self, task_id: str, actual_outcome: str):
        for decision in reversed(self.decisions):
            if decision.task_id == task_id and decision.actual_outcome is None:
                decision.actual_outcome = actual_outcome
                break

    def compute_truth_metrics(self) -> GovernanceTruthMetrics:
        if not self.decisions:
            return GovernanceTruthMetrics(
                total_decisions=0, approvals=0, blocks=0, conditionals=0, fallbacks=0,
                false_positive_rate=0.0, false_negative_rate=0.0, over_conservative_rate=0.0,
                under_conservative_rate=0.0, accuracy=0.0, issues=["No governance decisions recorded"]
            )

        total = len(self.decisions)
        approvals = sum(1 for d in self.decisions if d.decision == "approved")
        blocks = sum(1 for d in self.decisions if d.decision == "blocked")
        conditionals = sum(1 for d in self.decisions if d.decision == "conditional")
        fallbacks = sum(1 for d in self.decisions if d.decision == "fallback")

        decisions_with_outcome = [d for d in self.decisions if d.actual_outcome is not None]
        if decisions_with_outcome:
            fp = fn = 0
            for d in decisions_with_outcome:
                if d.decision == "blocked" and d.actual_outcome in ("success", "partial"):
                    fp += 1
                elif d.decision == "approved" and d.actual_outcome in ("failure", "harmful"):
                    fn += 1
            false_positive_rate = fp / len(decisions_with_outcome) if decisions_with_outcome else 0.0
            false_negative_rate = fn / len(decisions_with_outcome) if decisions_with_outcome else 0.0
            accuracy = (len(decisions_with_outcome) - fp - fn) / len(decisions_with_outcome) if decisions_with_outcome else 0.0
        else:
            false_positive_rate = false_negative_rate = accuracy = 0.0

        over_conservative_rate = blocks / total if total > 0 else 0.0
        under_conservative_rate = (approvals - fn) / total if total > 0 else 0.0

        issues = []
        if false_positive_rate > 0.3:
            issues.append(f"High false positive rate ({false_positive_rate:.1%}) - governor too conservative")
        if false_negative_rate > 0.1:
            issues.append(f"High false negative rate ({false_negative_rate:.1%}) - governor too permissive")
        if accuracy < 0.6:
            issues.append(f"Low accuracy ({accuracy:.1%}) - governance decisions unreliable")

        return GovernanceTruthMetrics(
            total_decisions=total, approvals=approvals, blocks=blocks,
            conditionals=conditionals, fallbacks=fallbacks,
            false_positive_rate=false_positive_rate, false_negative_rate=false_negative_rate,
            over_conservative_rate=over_conservative_rate, under_conservative_rate=under_conservative_rate,
            accuracy=accuracy, issues=issues
        )


# ==============================================================================
# Combined Truth Report
# ==============================================================================

@dataclass
class TruthReport:
    timestamp: str
    utility: UtilityTruthMetrics
    routing: RoutingQualityMetrics
    governance: GovernanceTruthMetrics
    overall_truth_score: float
    critical_issues: List[str]
    recommendations: List[str]


class TruthValidator:
    def __init__(self):
        self.utility_validator = UtilityTruthValidator()
        self.routing_validator = RoutingTruthValidator()
        self.governance_validator = GovernanceTruthValidator()

    def record_utility_prediction(self, task_id: str, agent_id: str, expected_utility: float,
                                 utility_inputs: List[float] = None, context: Dict[str, Any] = None):
        self.utility_validator.record_prediction(task_id, agent_id, expected_utility, utility_inputs, context)

    def record_utility_outcome(self, task_id: str, agent_id: str, actual_outcome: float, outcome_type: str = "success"):
        self.utility_validator.record_outcome(task_id, agent_id, actual_outcome, outcome_type)

    def record_routing(self, task_id: str, chosen_agent: str, context: str = "",
                      available_agents: List[str] = None, reasoning: str = ""):
        self.routing_validator.record_routing(task_id, chosen_agent, context, available_agents, reasoning)

    def record_governance(self, task_id: str, proposed_action: str, decision: str,
                         constraints_checked: List[str], reason: str, actual_outcome: str = None):
        self.governance_validator.record_decision(task_id, proposed_action, decision,
                                                 constraints_checked, reason, actual_outcome)

    def run_validation(self) -> TruthReport:
        utility_metrics = self.utility_validator.compute_truth_metrics()
        routing_metrics = self.routing_validator.compute_quality_metrics()
        governance_metrics = self.governance_validator.compute_truth_metrics()

        utility_score = utility_metrics.honesty_score if utility_metrics.total_predictions > 0 else 1.0
        routing_score = routing_metrics.consistency_rate
        governance_score = 1.0 - (governance_metrics.false_positive_rate + governance_metrics.false_negative_rate) / 2
        overall_truth_score = (utility_score * 0.5 + routing_score * 0.25 + governance_score * 0.25)

        all_issues = utility_metrics.issues + routing_metrics.issues + governance_metrics.issues
        critical_issues = [i for i in all_issues if any(kw in i.lower() for kw in ["low", "high", "risk", "collapse"])]

        recommendations = []
        if utility_metrics.honesty_score < 0.7:
            recommendations.append("URGENT: Calibrate utility function - predictions unreliable")
        if routing_metrics.consistency_rate < 0.7:
            recommendations.append("Calibrate routing - oscillating between agents")
        if governance_metrics.false_positive_rate > 0.2:
            recommendations.append("Review governor thresholds - too conservative")
        if governance_metrics.false_negative_rate > 0.05:
            recommendations.append("CRITICAL: Governor missing dangerous actions - fix immediately")

        return TruthReport(
            timestamp=datetime.now().isoformat(), utility=utility_metrics,
            routing=routing_metrics, governance=governance_metrics,
            overall_truth_score=overall_truth_score, critical_issues=critical_issues,
            recommendations=recommendations
        )

    def generate_report(self) -> str:
        report = self.run_validation()
        lines = [
            "=" * 70,
            "TRUTH VALIDATION REPORT",
            "=" * 70,
            f"Timestamp: {report.timestamp}",
            f"Overall Truth Score: {report.overall_truth_score:.1%}",
            "",
            "【Utility Truth Metrics】",
            f"  Total Predictions: {report.utility.total_predictions}",
            f"  Honesty Score: {report.utility.honesty_score:.1%}",
            f"  Overestimated: {report.utility.overestimated}, Underestimated: {report.utility.underestimated}",
            f"  Mean Delta: {report.utility.mean_delta:+.3f}, Std: {report.utility.std_delta:.3f}",
            f"  Collapse Risk: {report.utility.collapse_risk:.1%}",
            f"  Reward Hack Risk: {report.utility.reward_hack_risk:.1%}",
        ]
        if report.utility.issues:
            for issue in report.utility.issues:
                lines.append(f"  ! {issue}")
        lines.extend([
            "",
            "【Routing Truth Metrics】",
            f"  Total Decisions: {report.routing.total_routing_decisions}",
            f"  Consistency Rate: {report.routing.consistency_rate:.1%}",
            f"  Agent Selection Entropy: {report.routing.agent_selection_entropy:.2f}",
            f"  Redundancy Score: {report.routing.redundancy_score:.1%}",
        ])
        if report.routing.issues:
            for issue in report.routing.issues:
                lines.append(f"  ! {issue}")
        lines.extend([
            "",
            "【Governance Truth Metrics】",
            f"  Total Decisions: {report.governance.total_decisions}",
            f"  Approvals: {report.governance.approvals}, Blocks: {report.governance.blocks}",
            f"  False Positive Rate: {report.governance.false_positive_rate:.1%}",
            f"  False Negative Rate: {report.governance.false_negative_rate:.1%}",
            f"  Accuracy: {report.governance.accuracy:.1%}",
        ])
        if report.governance.issues:
            for issue in report.governance.issues:
                lines.append(f"  ! {issue}")
        lines.extend([
            "",
            "【Critical Issues】",
        ])
        if report.critical_issues:
            for issue in report.critical_issues:
                lines.append(f"  ! {issue}")
        else:
            lines.append("  None")
        lines.extend(["", "【Recommendations】"])
        if report.recommendations:
            for rec in report.recommendations:
                lines.append(f"  -> {rec}")
        else:
            lines.append("  System truth metrics within acceptable range")
        lines.extend(["", "=" * 70])
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 70)
    print("Truth Metrics - Scientific Validation System")
    print("=" * 70)

    validator = TruthValidator()

    print("\n[1] Recording utility predictions + outcomes...")
    validator.record_utility_prediction("task_001", "coder", 0.85, [0.8, 0.6], {"type": "feature"})
    validator.record_utility_outcome("task_001", "coder", 0.4, "partial")
    validator.record_utility_prediction("task_002", "reviewer", 0.5, [0.4, 0.3], {"type": "review"})
    validator.record_utility_outcome("task_002", "reviewer", 0.75, "success")
    validator.record_utility_prediction("task_003", "planner", 0.7, [0.6, 0.5], {"type": "planning"})
    validator.record_utility_outcome("task_003", "planner", 0.68, "success")
    validator.record_utility_prediction("task_004", "tester", 0.9, [0.85, 0.7], {"type": "test"})
    validator.record_utility_outcome("task_004", "tester", 0.35, "failure")
    print("    4 predictions recorded")

    print("\n[2] Recording routing decisions...")
    validator.record_routing("task_001", "coder", "high_complexity", ["planner", "coder", "reviewer"], "complex task")
    validator.record_routing("task_002", "reviewer", "low_complexity", ["planner", "reviewer"], "simple review")
    validator.record_routing("task_001", "coder", "high_complexity", ["planner", "coder", "reviewer"], "complex task")
    validator.record_routing("task_001", "reviewer", "high_complexity", ["planner", "coder", "reviewer"], "complex task")
    validator.routing_validator.register_agent_capability("planner", ["plan", "design", "coordinate"])
    validator.routing_validator.register_agent_capability("coder", ["write", "refactor", "debug"])
    validator.routing_validator.register_agent_capability("reviewer", ["review", "analyze"])
    validator.routing_validator.register_agent_capability("tester", ["test", "validate"])
    print("    4 routing decisions recorded")

    print("\n[3] Recording governance decisions...")
    validator.record_governance("task_001", "deploy_to_prod", "blocked", ["safety", "compliance"], "Safety check failed", "failure")
    validator.record_governance("task_002", "write_test", "approved", [], "Normal operation", "success")
    validator.record_governance("task_003", "refactor_core", "conditional", ["backup", "rollback"], "Needs backup", "partial")
    validator.record_governance("task_004", "deploy_to_prod", "approved", ["safety", "compliance"], "All checks passed", "failure")
    print("    4 governance decisions recorded")

    print("\n[4] Running Truth Validation...")
    print("\n" + validator.generate_report())
