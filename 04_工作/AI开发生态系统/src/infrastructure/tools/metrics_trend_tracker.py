#!/usr/bin/env python3
"""
Metrics Trend Tracker - Phase: Reality Alignment
持续监控关键统计量趋势

核心统计量：
1. Calibration Trend: ECE(t) - 是否收敛、震荡、漂移
2. Governance Pressure Curve: block_rate(t), conditional_rate(t), override_rate(t)
3. Routing Entropy: entropy(agent_selection) - 防止路由塌缩
4. Human Trust Score: trust = 1 - override_rate (按task_type)
"""

import sys
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import json
import threading

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


@dataclass
class CalibrationMetric:
    timestamp: str
    task_type: str
    ece: float
    sample_count: int


@dataclass
class GovernanceMetric:
    timestamp: str
    total_decisions: int
    approved: int
    blocked: int
    conditional: int
    block_rate: float
    conditional_rate: float
    override_rate: float


@dataclass
class RoutingMetric:
    timestamp: str
    agent_distribution: Dict[str, int]
    entropy: float
    concentration: float
    total_selections: int


@dataclass
class TrustMetric:
    timestamp: str
    task_type: str
    override_count: int
    total_count: int
    trust_score: float


class TrendAnalyzer:
    @staticmethod
    def detect_convergence(values: List[float], window: int = 5) -> Dict[str, Any]:
        if len(values) < window:
            return {"converged": False, "reason": "insufficient_data"}
        recent = values[-window:]
        mean = statistics.mean(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else float('inf')
        cv = stdev / mean if mean > 0 else float('inf')
        return {"converged": cv < 0.1, "mean": mean, "stdev": stdev, "cv": cv}

    @staticmethod
    def detect_drift(values: List[float], baseline_window: int = 10) -> Dict[str, Any]:
        if len(values) < baseline_window * 2:
            return {"has_drift": False, "reason": "insufficient_data"}
        baseline = statistics.mean(values[:baseline_window])
        current = statistics.mean(values[-baseline_window:])
        drift_magnitude = abs(current - baseline)
        drift_percent = (drift_magnitude / baseline * 100) if baseline > 0 else 0
        return {"has_drift": drift_percent > 20, "baseline": baseline, "current": current,
                "drift_percent": drift_percent}

    @staticmethod
    def detect_oscillation(values: List[float]) -> Dict[str, Any]:
        if len(values) < 10:
            return {"has_oscillation": False}
        directions = [1 if values[i] > values[i-1] else -1 if values[i] < values[i-1] else 0 for i in range(1, len(values))]
        changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i-1])
        change_rate = changes / (len(directions) - 1) if len(directions) > 1 else 0
        return {"has_oscillation": change_rate > 0.7, "change_rate": change_rate}


class MetricsTrendTracker:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/trends"
        self._ensure_storage_dir()
        self.calibration_metrics: List[CalibrationMetric] = []
        self.governance_metrics: List[GovernanceMetric] = []
        self.routing_metrics: List[RoutingMetric] = []
        self.trust_metrics: List[TrustMetric] = []
        self._lock = threading.Lock()
        self._override_counts: Dict[str, int] = defaultdict(int)
        self._total_counts: Dict[str, int] = defaultdict(int)

    def _ensure_storage_dir(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def record_ece(self, task_type: str, ece: float, sample_count: int):
        with self._lock:
            self.calibration_metrics.append(CalibrationMetric(
                timestamp=datetime.now().isoformat(), task_type=task_type,
                ece=ece, sample_count=sample_count))

    def record_governance(self, total_decisions: int, approved: int, blocked: int,
                          conditional: int, override_count: int = 0):
        with self._lock:
            self.governance_metrics.append(GovernanceMetric(
                timestamp=datetime.now().isoformat(), total_decisions=total_decisions,
                approved=approved, blocked=blocked, conditional=conditional,
                block_rate=blocked/total_decisions if total_decisions > 0 else 0,
                conditional_rate=conditional/total_decisions if total_decisions > 0 else 0,
                override_rate=override_count/total_decisions if total_decisions > 0 else 0))

    def record_routing(self, agent_distribution: Dict[str, int]):
        with self._lock:
            total = sum(agent_distribution.values())
            entropy = self._compute_entropy(agent_distribution, total)
            concentration = max(agent_distribution.values())/total if total > 0 and agent_distribution else 0
            self.routing_metrics.append(RoutingMetric(
                timestamp=datetime.now().isoformat(), agent_distribution=agent_distribution,
                entropy=entropy, concentration=concentration, total_selections=total))

    def record_trust(self, task_type: str, override_count: int, total_count: int):
        trust_score = 1.0 - (override_count / total_count) if total_count > 0 else 0.0
        self.trust_metrics.append(TrustMetric(
            timestamp=datetime.now().isoformat(), task_type=task_type,
            override_count=override_count, total_count=total_count, trust_score=trust_score))

    def _compute_entropy(self, distribution: Dict[str, int], total: int) -> float:
        if total == 0:
            return 0.0
        entropy = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                entropy -= p * (p ** 0.5)
        return max(0.0, min(1.0, entropy + 1.0))

    def _get_trend_direction(self, values: List[float]) -> str:
        if len(values) < 2:
            return "stable"
        first, last = values[0], values[-1]
        change = (last - first) / first if first > 0 else 0
        if change > 0.05:
            return "increasing"
        elif change < -0.05:
            return "decreasing"
        return "stable"

    def _assess_pressure_status(self, block_rates: List[float], override_rates: List[float]) -> str:
        if not block_rates or not override_rates:
            return "unknown"
        recent_block = statistics.mean(block_rates[-5:]) if len(block_rates) >= 5 else statistics.mean(block_rates)
        recent_override = statistics.mean(override_rates[-5:]) if len(override_rates) >= 5 else statistics.mean(override_rates)
        if recent_block > 0.4:
            return "too_restrictive"
        elif recent_block < 0.05 and recent_override < 0.05:
            return "too_permissive"
        elif recent_override > recent_block * 2:
            return "override_heavy"
        return "healthy"

    def get_calibration_trend(self, task_type: str = None, window: int = 30) -> Dict[str, Any]:
        metrics = self.calibration_metrics
        if task_type:
            metrics = [m for m in metrics if m.task_type == task_type]
        if not metrics:
            return {"error": "no_data"}
        recent = metrics[-window:]
        ece_values = [m.ece for m in recent]
        return {
            "task_type": task_type or "all",
            "sample_count": len(recent),
            "current_ece": ece_values[-1] if ece_values else 0,
            "mean_ece": statistics.mean(ece_values) if ece_values else 0,
            "convergence": TrendAnalyzer.detect_convergence(ece_values),
            "drift": TrendAnalyzer.detect_drift(ece_values),
            "oscillation": TrendAnalyzer.detect_oscillation(ece_values),
            "trend_direction": "improving" if ece_values and ece_values[-1] < ece_values[0] else "degrading"
        }

    def get_governance_pressure_curve(self, window: int = 30) -> Dict[str, Any]:
        if not self.governance_metrics:
            return {"error": "no_data"}
        recent = self.governance_metrics[-window:]
        block_rates = [m.block_rate for m in recent]
        conditional_rates = [m.conditional_rate for m in recent]
        override_rates = [m.override_rate for m in recent]
        return {
            "sample_count": len(recent),
            "block_rate": {"current": block_rates[-1] if block_rates else 0, "mean": statistics.mean(block_rates) if block_rates else 0,
                           "trend": self._get_trend_direction(block_rates), "history": block_rates[-20:]},
            "conditional_rate": {"current": conditional_rates[-1] if conditional_rates else 0, "mean": statistics.mean(conditional_rates) if conditional_rates else 0,
                                 "trend": self._get_trend_direction(conditional_rates), "history": conditional_rates[-20:]},
            "override_rate": {"current": override_rates[-1] if override_rates else 0, "mean": statistics.mean(override_rates) if override_rates else 0,
                              "trend": self._get_trend_direction(override_rates), "history": override_rates[-20:]},
            "pressure_status": self._assess_pressure_status(block_rates, override_rates)
        }

    def get_routing_entropy_trend(self, window: int = 30) -> Dict[str, Any]:
        if not self.routing_metrics:
            return {"error": "no_data"}
        recent = self.routing_metrics[-window:]
        entropies = [m.entropy for m in recent]
        concentrations = [m.concentration for m in recent]
        return {
            "sample_count": len(recent),
            "current_entropy": entropies[-1] if entropies else 0,
            "mean_entropy": statistics.mean(entropies) if entropies else 0,
            "current_concentration": concentrations[-1] if concentrations else 0,
            "mean_concentration": statistics.mean(concentrations) if concentrations else 0,
            "entropy_trend": self._get_trend_direction(entropies),
            "concentration_trend": self._get_trend_direction(concentrations),
            "drift": TrendAnalyzer.detect_drift(entropies),
            "collapse_risk": entropies[-1] < 0.3 if entropies else False,
            "entropy_history": entropies[-20:],
            "concentration_history": concentrations[-20:]
        }

    def get_human_trust_score(self, task_type: str = None) -> Dict[str, Any]:
        metrics = self.trust_metrics
        if task_type:
            metrics = [m for m in metrics if m.task_type == task_type]
        if not metrics:
            return {"error": "no_data"}
        by_type = defaultdict(list)
        for m in metrics:
            by_type[m.task_type].append(m)
        trust_scores = {}
        for tt, tt_metrics in by_type.items():
            recent = tt_metrics[-20:]
            trust_scores[tt] = {
                "current": recent[-1].trust_score if recent else 0,
                "mean": statistics.mean(m.trust_score for m in recent) if recent else 0,
                "trend": self._get_trend_direction([m.trust_score for m in recent]),
                "override_count": recent[-1].override_count if recent else 0,
                "total_count": recent[-1].total_count if recent else 0
            }
        return {"by_task_type": trust_scores, "overall_trust": statistics.mean([ts["mean"] for ts in trust_scores.values()]) if trust_scores else 0}

    def generate_trend_report(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.now().isoformat(),
            "calibration_trend": {tt: self.get_calibration_trend(tt) for tt in ["build", "deploy", "delete", "research", "fix", "review"]},
            "governance_pressure": self.get_governance_pressure_curve(),
            "routing_entropy": self.get_routing_entropy_trend(),
            "human_trust": self.get_human_trust_score(),
            "alerts": self._generate_alerts()
        }

    def _generate_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for tt in ["build", "deploy", "delete", "research", "fix", "review"]:
            trend = self.get_calibration_trend(tt)
            if "error" not in trend and trend.get("drift", {}).get("has_drift"):
                alerts.append({"severity": "high", "type": "calibration_drift",
                               "message": f"{tt}: ECE漂移{trend['drift']['drift_percent']:.1f}%"})
        routing = self.get_routing_entropy_trend()
        if "error" not in routing and routing.get("collapse_risk"):
            alerts.append({"severity": "critical", "type": "routing_collapse",
                           "message": f"路由塌缩风险: entropy={routing['current_entropy']:.3f}"})
        gov = self.get_governance_pressure_curve()
        if "error" not in gov:
            status = gov.get("pressure_status", "unknown")
            if status != "healthy":
                alerts.append({"severity": "high" if status != "too_permissive" else "medium", "type": "governance_pressure",
                               "message": f"Governance压力: {status}"})
        return alerts

    def save(self, date: str = None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        path = f"{self.storage_path}/trends_{date}.json"
        with open(path, 'w') as f:
            json.dump({"date": date, "report": self.generate_trend_report()}, f, indent=2)
        return path


if __name__ == "__main__":
    print("=" * 70)
    print("METRICS TREND TRACKER - Reality Alignment")
    print("=" * 70)

    tracker = MetricsTrendTracker()

    print("\n[1] Recording simulated metrics (30 days)...")
    import random
    random.seed(42)

    for day in range(30):
        for task_type in ["build", "deploy", "delete", "research"]:
            base_ece = {"build": 0.08, "deploy": 0.30, "delete": 0.25, "research": 0.05}[task_type]
            ece = base_ece + random.gauss(0, 0.03)
            tracker.record_ece(task_type, max(0, ece), 20 + random.randint(0, 10))
        total = 50
        blocked = int(total * random.uniform(0.1, 0.3))
        conditional = int(total * random.uniform(0.2, 0.4))
        approved = total - blocked - conditional
        overrides = int(total * random.uniform(0.02, 0.15))
        tracker.record_governance(total, approved, blocked, conditional, overrides)
        dist = {"planner": random.randint(10, 20), "coder": random.randint(15, 25),
                "reviewer": random.randint(8, 18), "tester": random.randint(5, 15)}
        tracker.record_routing(dist)

    print("  Done")

    print("\n[2] Calibration Trend:")
    for tt in ["build", "deploy", "delete", "research"]:
        trend = tracker.get_calibration_trend(tt)
        if "error" not in trend:
            print(f"  {tt:8s}: ECE={trend['current_ece']:.3f}, trend={trend['trend_direction']}, converged={trend['convergence']['converged']}")

    print("\n[3] Governance Pressure:")
    gov = tracker.get_governance_pressure_curve()
    if "error" not in gov:
        print(f"  Block rate: {gov['block_rate']['mean']:.1%} ({gov['block_rate']['trend']})")
        print(f"  Override rate: {gov['override_rate']['mean']:.1%} ({gov['override_rate']['trend']})")
        print(f"  Status: {gov['pressure_status']}")

    print("\n[4] Routing Entropy:")
    routing = tracker.get_routing_entropy_trend()
    if "error" not in routing:
        print(f"  Entropy: {routing['current_entropy']:.3f} (trend: {routing['entropy_trend']})")
        print(f"  Concentration: {routing['current_concentration']:.3f}")
        print(f"  Collapse risk: {routing['collapse_risk']}")

    print("\n[5] Human Trust Score:")
    trust = tracker.get_human_trust_score()
    if "error" not in trust:
        for tt, ts in trust.get("by_task_type", {}).items():
            override_rate = ts['override_count']/max(1, ts['total_count'])
            print(f"  {tt:8s}: trust={ts['mean']:.3f} (override_rate={override_rate:.1%})")

    print("\n[6] Alerts:")
    report = tracker.generate_trend_report()
    for alert in report.get("alerts", []):
        print(f"  [{alert['severity']}] {alert['type']}: {alert['message']}")

    print("\n" + "=" * 70)
    print("KEY INSIGHT: 趋势比单次测量更重要")
    print("=" * 70)