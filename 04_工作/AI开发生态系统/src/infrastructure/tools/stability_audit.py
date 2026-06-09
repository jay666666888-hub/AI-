#!/usr/bin/env python3
"""
System Stability Observer - Observer Layer
不参与决策，只观察系统运行结果轨迹

核心职责：
① Drift Curve - policy drift slope, variance growth rate
② Goal Entropy - Shannon entropy over goals, convergence ratio
③ Collapse Detection - 单策略 dominance, goal narrowing, routing collapse
"""

import sys
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


@dataclass
class DriftCurveResult:
    """Drift Curve Analysis"""
    is_stable: bool
    policy_drift_slope: float  # per unit time, positive = degrading
    variance_growth_rate: float
    drift_direction: str  # "improving" / "stable" / "degrading"
    issues: List[str]


@dataclass
class GoalEntropyResult:
    """Goal Entropy Analysis"""
    is_healthy: bool
    entropy_score: float  # 0 = single goal, high = many goals
    convergence_ratio: float  # 1 = fully convergent, 0 = fully divergent
    goal_distribution: Dict[str, int]
    issues: List[str]


@dataclass
class CollapseDetectionResult:
    """Collapse Detection"""
    collapse_detected: bool
    single_strategy_dominance: float  # 0-1, >0.8 = collapse
    goal_narrowing_rate: float
    routing_collapse: bool
    dominant_strategies: List[str]
    issues: List[str]


@dataclass
class StabilityAuditReport:
    timestamp: str
    drift_curve: DriftCurveResult
    goal_entropy: GoalEntropyResult
    collapse: CollapseDetectionResult
    overall_healthy: bool
    severity: str


class DriftCurveAnalyzer:
    """
    分析 drift curve
    - policy drift slope
    - variance growth rate
    """

    def __init__(self):
        self.policy_scores: List[Tuple[datetime, float]] = []
        self.variance_history: List[float] = []

    def record_policy_score(self, timestamp: datetime, score: float):
        """记录 policy score"""
        self.policy_scores.append((timestamp, score))

    def compute_drift_slope(self) -> float:
        """
        计算 policy drift slope
        正数 = 随时间变差（drift）
        负数 = 随时间变好
        """
        if len(self.policy_scores) < 10:
            return 0.0

        # 使用线性回归计算 slope
        n = len(self.policy_scores)
        times = [(t - self.policy_scores[0][0]).total_seconds() for t, _ in self.policy_scores]
        scores = [s for _, s in self.policy_scores]

        mean_t = sum(times) / n
        mean_s = sum(scores) / n

        numerator = sum((t - mean_t) * (s - mean_s) for t, s in zip(times, scores))
        denominator = sum((t - mean_t) ** 2 for t in times)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # 归一化（每秒的 drift）
        return slope * 86400  # 转换为每天

    def compute_variance_growth(self) -> float:
        """
        计算 variance growth rate
        """
        if len(self.policy_scores) < 20:
            return 0.0

        # 分窗口计算 variance
        window_size = 10
        variances = []

        for i in range(len(self.policy_scores) - window_size):
            window_scores = [s for _, s in self.policy_scores[i:i+window_size]]
            mean = sum(window_scores) / len(window_scores)
            var = sum((s - mean) ** 2 for s in window_scores) / len(window_scores)
            variances.append(var)

        if len(variances) < 2:
            return 0.0

        # 计算 variance 的增长率
        early_var = sum(variances[:len(variances)//2]) / (len(variances)//2)
        late_var = sum(variances[len(variances)//2:]) / (len(variances) - len(variances)//2)

        if early_var == 0:
            return 0.0

        return (late_var - early_var) / early_var

    def analyze(self) -> DriftCurveResult:
        slope = self.compute_drift_slope()
        variance_growth = self.compute_variance_growth()

        issues = []

        # 判断 drift direction
        drift_direction = "stable"
        if slope > 0.01:
            drift_direction = "degrading"
            issues.append(f"Policy drift detected (slope: {slope:.4f}/day)")
        elif slope < -0.01:
            drift_direction = "improving"

        # 判断 variance growth
        if variance_growth > 0.5:
            issues.append(f"High variance growth ({variance_growth:.1%})")

        is_stable = len(issues) == 0 and abs(slope) < 0.01

        return DriftCurveResult(
            is_stable=is_stable,
            policy_drift_slope=slope,
            variance_growth_rate=variance_growth,
            drift_direction=drift_direction,
            issues=issues
        )


class GoalEntropyAnalyzer:
    """
    分析 goal entropy
    - Shannon entropy over goals
    - convergence ratio
    """

    def __init__(self):
        self.goal_history: List[Tuple[datetime, str]] = []

    def record_goal(self, timestamp: datetime, goal: str):
        """记录 goal 选择"""
        self.goal_history.append((timestamp, goal))

    def compute_shannon_entropy(self, window_size: int = 50) -> float:
        """
        计算 Shannon entropy
        0 = 单 goal（完全收敛）
        高 = 均匀分布（完全发散）
        """
        if len(self.goal_history) < window_size:
            return 0.0

        # 使用最近 window_size 个 goal
        recent_goals = [g for _, g in self.goal_history[-window_size:]]
        counter = Counter(recent_goals)
        total = len(recent_goals)

        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # 归一化（最大 entropy = log2(n_goals)）
        n_unique = len(counter)
        max_entropy = math.log2(n_unique) if n_unique > 1 else 1

        return entropy / max_entropy if max_entropy > 0 else 0.0

    def compute_convergence_ratio(self, window_size: int = 50) -> float:
        """
        计算收敛比
        1 = 所有 goal 都是同一个
        0 = 完全均匀分布
        """
        if len(self.goal_history) < window_size:
            return 1.0

        recent_goals = [g for _, g in self.goal_history[-window_size:]]
        counter = Counter(recent_goals)

        most_common_count = counter.most_common(1)[0][1]
        return most_common_count / len(recent_goals)

    def get_goal_distribution(self) -> Dict[str, int]:
        """获取 goal 分布"""
        return dict(Counter(g for _, g in self.goal_history))

    def analyze(self) -> GoalEntropyResult:
        entropy = self.compute_shannon_entropy()
        convergence = self.compute_convergence_ratio()
        distribution = self.get_goal_distribution()

        issues = []

        if entropy > 0.8:
            issues.append(f"High goal entropy ({entropy:.2f}) - too分散")

        if convergence < 0.3:
            issues.append(f"Low convergence ({convergence:.1%}) - goal wandering")

        is_healthy = len(issues) == 0 and entropy < 0.7 and convergence > 0.4

        return GoalEntropyResult(
            is_healthy=is_healthy,
            entropy_score=entropy,
            convergence_ratio=convergence,
            goal_distribution=distribution,
            issues=issues
        )


class CollapseDetector:
    """
    检测 collapse
    - 单策略 dominance
    - goal narrowing
    - routing collapse
    """

    def __init__(self):
        self.strategy_history: List[Tuple[datetime, str]] = []
        self.goal_width_history: List[Tuple[datetime, int]] = []
        self.routing_history: List[List[str]] = []

    def record_strategy(self, timestamp: datetime, strategy: str):
        """记录使用的策略"""
        self.strategy_history.append((timestamp, strategy))

    def record_goal_width(self, timestamp: datetime, num_goals: int):
        """记录 goal 宽度（多少个不同 goal）"""
        self.goal_width_history.append((timestamp, num_goals))

    def record_routing(self, routing_path: List[str]):
        """记录 routing 路径"""
        self.routing_history.append(routing_path)

    def compute_strategy_dominance(self, window_size: int = 100) -> float:
        """
        计算策略 dominance
        >0.8 = collapse（单一策略主导）
        """
        if len(self.strategy_history) < window_size:
            return 0.0

        recent = [s for _, s in self.strategy_history[-window_size:]]
        counter = Counter(recent)

        most_common_count = counter.most_common(1)[0][1]
        return most_common_count / len(recent)

    def compute_goal_narrowing_rate(self) -> float:
        """
        计算 goal narrowing rate
        正数 = goal 在变少（收敛）
        负数 = goal 在变多（发散）
        """
        if len(self.goal_width_history) < 20:
            return 0.0

        # 分成前后两半，计算平均 width
        mid = len(self.goal_width_history) // 2
        early_avg = sum(w for _, w in self.goal_width_history[:mid]) / mid
        late_avg = sum(w for _, w in self.goal_width_history[mid:]) / (len(self.goal_width_history) - mid)

        if early_avg == 0:
            return 0.0

        return (late_avg - early_avg) / early_avg

    def detect_routing_collapse(self, threshold: float = 0.95) -> bool:
        """
        检测 routing collapse
        如果 >95% 的执行都是同一个 path = collapse
        """
        if len(self.routing_history) < 10:
            return False

        path_counts = Counter(tuple(p) for p in self.routing_history)
        most_common_ratio = path_counts.most_common(1)[0][1] / len(self.routing_history)

        return most_common_ratio > threshold

    def get_dominant_strategies(self, top_n: int = 3) -> List[str]:
        """获取主导策略"""
        recent = [s for _, s in self.strategy_history[-100:]]
        counter = Counter(recent)
        return [s for s, _ in counter.most_common(top_n)]

    def analyze(self) -> CollapseDetectionResult:
        dominance = self.compute_strategy_dominance()
        narrowing = self.compute_goal_narrowing_rate()
        routing_collapse = self.detect_routing_collapse()
        dominant = self.get_dominant_strategies()

        issues = []

        if dominance > 0.8:
            issues.append(f"Single strategy dominance ({dominance:.1%}) - collapse")

        if narrowing < -0.3:
            issues.append(f"Goal narrowing negative ({narrowing:.1%}) - unstable expansion")

        if routing_collapse:
            issues.append("Routing collapse detected - same path used >95%")

        collapse_detected = len(issues) > 0

        return CollapseDetectionResult(
            collapse_detected=collapse_detected,
            single_strategy_dominance=dominance,
            goal_narrowing_rate=narrowing,
            routing_collapse=routing_collapse,
            dominant_strategies=dominant,
            issues=issues
        )


class StabilityAudit:
    """
    System Stability Observer
    不参与决策，只观察系统运行结果轨迹
    """

    def __init__(self):
        self.drift_analyzer = DriftCurveAnalyzer()
        self.entropy_analyzer = GoalEntropyAnalyzer()
        self.collapse_detector = CollapseDetector()
        self.audit_start = datetime.now().isoformat()

    def record_policy_score(self, score: float):
        self.drift_analyzer.record_policy_score(datetime.now(), score)

    def record_goal(self, goal: str):
        self.entropy_analyzer.record_goal(datetime.now(), goal)

    def record_strategy(self, strategy: str):
        self.collapse_detector.record_strategy(datetime.now(), strategy)

    def record_goal_width(self, num_goals: int):
        self.collapse_detector.record_goal_width(datetime.now(), num_goals)

    def record_routing(self, routing_path: List[str]):
        self.collapse_detector.record_routing(routing_path)

    def run_audit(self) -> StabilityAuditReport:
        drift_result = self.drift_analyzer.analyze()
        entropy_result = self.entropy_analyzer.analyze()
        collapse_result = self.collapse_detector.analyze()

        all_healthy = (
            drift_result.is_stable and
            entropy_result.is_healthy and
            not collapse_result.collapse_detected
        )

        severity = "OK"
        if collapse_result.collapse_detected:
            severity = "CRITICAL"
        elif not drift_result.is_stable or not entropy_result.is_healthy:
            severity = "WARNING"

        return StabilityAuditReport(
            timestamp=self.audit_start,
            drift_curve=drift_result,
            goal_entropy=entropy_result,
            collapse=collapse_result,
            overall_healthy=all_healthy,
            severity=severity
        )

    def generate_report(self) -> str:
        report = self.run_audit()
        lines = [
            "=" * 60,
            "SYSTEM STABILITY OBSERVER - Audit Report",
            "=" * 60,
            f"Timestamp: {report.timestamp}",
            f"Overall Status: {report.severity}",
            "",
            "【① Drift Curve】",
            f"  Stable: {report.drift_curve.is_stable}",
            f"  Drift Slope: {report.drift_curve.policy_drift_slope:.4f}/day",
            f"  Variance Growth: {report.drift_curve.variance_growth_rate:.1%}",
            f"  Direction: {report.drift_curve.drift_direction}",
        ]
        if report.drift_curve.issues:
            for issue in report.drift_curve.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")

        lines.extend([
            "",
            "【② Goal Entropy】",
            f"  Healthy: {report.goal_entropy.is_healthy}",
            f"  Entropy Score: {report.goal_entropy.entropy_score:.3f}",
            f"  Convergence: {report.goal_entropy.convergence_ratio:.1%}",
            f"  Goal Distribution: {list(report.goal_entropy.goal_distribution.keys())[:5]}",
        ])
        if report.goal_entropy.issues:
            for issue in report.goal_entropy.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")

        lines.extend([
            "",
            "【③ Collapse Detection】",
            f"  Collapse: {report.collapse.collapse_detected}",
            f"  Strategy Dominance: {report.collapse.single_strategy_dominance:.1%}",
            f"  Goal Narrowing: {report.collapse.goal_narrowing_rate:.1%}",
            f"  Routing Collapse: {report.collapse.routing_collapse}",
            f"  Dominant Strategies: {report.collapse.dominant_strategies[:3]}",
        ])
        if report.collapse.issues:
            for issue in report.collapse.issues:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append("  ✓ No issues")

        lines.extend(["", "=" * 60, f"Final Verdict: {report.severity}", "=" * 60])
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("System Stability Observer - Starting Audit")
    print("=" * 60)

    audit = StabilityAudit()

    print("\n[1] Generating test data...")
    import random
    from datetime import timedelta

    base_time = datetime.now()

    # 模拟 100 天的 policy scores
    for i in range(100):
        # 模拟轻微 drift（变差）
        score = 0.7 + random.gauss(-0.001 * i, 0.1)
        score = max(0.1, min(0.9, score))
        audit.record_policy_score(score)

    # 模拟 goal entropy
    goals = ["improve_speed", "reduce_cost", "enhance_quality", "ensure_safety", "optimizeUX"]
    for i in range(100):
        # 模拟逐渐收敛到 2 个 goal
        if i < 50:
            goal = random.choice(goals)
        else:
            goal = random.choice(goals[:2])  # 收敛
        audit.record_goal(goal)

    # 模拟策略 dominance
    strategies = ["aggressive", "conservative", "balanced"]
    for i in range(100):
        # 模拟逐渐 dominance
        if i < 70:
            strategy = random.choice(strategies)
        else:
            strategy = "aggressive"  # collapse
        audit.record_strategy(strategy)

    # 模拟 goal width
    for i in range(100):
        if i < 50:
            width = random.randint(3, 5)
        else:
            width = random.randint(1, 2)  # narrowing
        audit.record_goal_width(width)

    # 模拟 routing
    paths = [["planner", "coder", "reviewer"],
             ["planner", "coder", "tester"],
             ["planner", "designer", "coder"]]
    for i in range(50):
        if i < 40:
            path = random.choice(paths)
        else:
            path = paths[0]  # collapse
        audit.record_routing(path)

    print("    Generated 100 time steps of data")

    print("\n[2] Running audit...")
    report = audit.run_audit()

    print(f"\n[3] Results:")
    print(f"    Overall: {report.severity}")
    print(f"    Drift Stable: {report.drift_curve.is_stable}")
    print(f"    Goal Healthy: {report.goal_entropy.is_healthy}")
    print(f"    Collapse: {report.collapse.collapse_detected}")

    print("\n" + audit.generate_report())
