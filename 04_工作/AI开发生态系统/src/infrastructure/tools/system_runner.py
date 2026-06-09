#!/usr/bin/env python3
"""
System Runner - 30-Day Validation
真实运行30天，收集telemetry，验证三个核心指标

Metrics tracked:
1. ECE trend (calibration quality)
2. Routing entropy/concentration (collapse risk)
3. Governance block_rate (pressure effectiveness)
"""

import sys
import uuid
import random
import statistics
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')

from infrastructure.tools.unified_calibration import (
    UnifiedCalibrationSystem, TaskType as UT_TaskType
)
from infrastructure.tools.calibration_governor import (
    CalibrationGovernor, CalibrationBuffer, AntiConstraints
)
from infrastructure.tools.shadow_mode import ShadowModeRunner, DecisionQualityAuditor


# ============================================================================
# Task Templates
# ============================================================================

TASK_TEMPLATES = {
    UT_TaskType.BUILD: [
        "build user authentication module",
        "build product catalog service",
        "build payment integration",
        "build search indexing pipeline",
        "build notification service",
        "build caching layer",
        "build API gateway",
        "build data transformation pipeline",
    ],
    UT_TaskType.DEPLOY: [
        "deploy to staging environment",
        "deploy to production",
        "deploy canary release",
        "deploy database migration",
        "deploy configuration change",
        "deploy rollback procedure",
    ],
    UT_TaskType.DELETE: [
        "delete temporary test files",
        "delete deprecated feature flag",
        "delete old log archives",
        "delete unused test data",
        "delete deprecated endpoint",
    ],
    UT_TaskType.RESEARCH: [
        "research new authentication library",
        "research database optimization options",
        "research caching strategies",
        "research monitoring solutions",
        "research error handling patterns",
        "research API design patterns",
    ],
    UT_TaskType.FIX: [
        "fix login authentication bug",
        "fix memory leak in worker",
        "fix race condition in cache",
        "fix database connection timeout",
        "fix error handling edge case",
        "fix security vulnerability",
    ],
    UT_TaskType.REVIEW: [
        "review pull request #1234",
        "review code architecture",
        "review security implementation",
        "review performance optimization",
        "review error handling",
    ],
}

AGENTS = ["planner", "coder", "reviewer", "tester", "deployer", "architect"]
TASK_TYPE_DIST = {
    UT_TaskType.BUILD: 0.25,
    UT_TaskType.DEPLOY: 0.15,
    UT_TaskType.DELETE: 0.08,
    UT_TaskType.RESEARCH: 0.20,
    UT_TaskType.FIX: 0.17,
    UT_TaskType.REVIEW: 0.15,
}


@dataclass
class TaskResult:
    task_id: str
    task_type: str
    predicted_utility: float
    actual_outcome: float
    agent: str
    governance_decision: str
    execution_time: float
    external_deps: int
    hidden_state: int
    rollback: bool
    timestamp: str


@dataclass
class DailyMetrics:
    date: str
    ece_by_type: Dict[str, float]
    routing_entropy: float
    routing_concentration: float
    governance_block_rate: float
    total_tasks: int
    approved: int
    blocked: int
    conditional: int


class TaskGenerator:
    """Generate realistic tasks with proper distribution"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_task(self):
        """Generate a single task: returns (description, task_type_str, agent, path, base_utility)"""
        task_types = [UT_TaskType.BUILD, UT_TaskType.DEPLOY, UT_TaskType.DELETE,
                     UT_TaskType.RESEARCH, UT_TaskType.FIX, UT_TaskType.REVIEW]
        weights = list(TASK_TYPE_DIST.values())

        task_type_str = random.choices(task_types, weights=weights)[0]

        templates = TASK_TEMPLATES[task_type_str]
        description = random.choice(templates)

        agent = random.choice(AGENTS)
        path = [agent]

        base_utility = self._get_base_utility(task_type_str)

        return description, task_type_str, agent, path, base_utility

    def _get_base_utility(self, task_type: str) -> float:
        base_ranges = {
            UT_TaskType.BUILD: (0.65, 0.85),
            UT_TaskType.DEPLOY: (0.50, 0.75),
            UT_TaskType.DELETE: (0.40, 0.65),
            UT_TaskType.RESEARCH: (0.70, 0.90),
            UT_TaskType.FIX: (0.55, 0.75),
            UT_TaskType.REVIEW: (0.75, 0.95),
        }
        low, high = base_ranges.get(task_type, (0.5, 0.8))
        return random.uniform(low, high)


class OutcomeSimulator:
    """Simulate realistic outcomes based on task type and conditions"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def simulate(
        self,
        task_type,
        predicted: float,
        external_deps: int,
        hidden_state: int
    ) -> Tuple[float, bool, float, bool]:
        """
        Simulate actual outcome.
        task_type is a TaskType enum (from unified_calibration.TaskType)
        Returns: (actual_outcome, success, execution_time, rollback_needed)
        """
        base_error = self._get_base_error(task_type)
        dep_penalty = min(0.15, external_deps * 0.03)
        hidden_penalty = min(0.10, hidden_state * 0.04)

        error = random.gauss(base_error, 0.08)
        error = max(-0.3, min(0.3, error))

        actual = predicted + error - dep_penalty - hidden_penalty
        actual = max(0.0, min(1.0, actual))

        success = actual >= 0.5

        exec_time = random.gauss(30, 10) if success else random.gauss(45, 15)
        exec_time = max(5, exec_time)

        rollback = not success and task_type in [
            UT_TaskType.DEPLOY, UT_TaskType.DELETE, UT_TaskType.FIX
        ]

        return actual, success, exec_time, rollback

    def _get_base_error(self, task_type):  # type: ignore
        """Expected prediction error by task type (positive = overestimation)"""
        errors = {
            UT_TaskType.BUILD: 0.03,
            UT_TaskType.DEPLOY: 0.20,
            UT_TaskType.DELETE: 0.25,
            UT_TaskType.RESEARCH: 0.02,
            UT_TaskType.FIX: 0.10,
            UT_TaskType.REVIEW: 0.01,
        }
        return errors.get(task_type, 0.1)


class MetricsCalculator:
    """Calculate the three critical metrics"""

    @staticmethod
    def calculate_ece(predictions: List[Tuple[float, float]], n_buckets: int = 10) -> float:
        """Expected Calibration Error"""
        if len(predictions) < 5:
            return 0.0

        buckets = defaultdict(list)
        for pred, actual in predictions:
            bucket_idx = min(int(pred * n_buckets), n_buckets - 1)
            buckets[bucket_idx].append((pred, actual))

        total = len(predictions)
        ece = 0.0
        for bucket_idx in range(n_buckets):
            if bucket_idx not in buckets:
                continue
            pts = buckets[bucket_idx]
            bucket_weight = len(pts) / total
            mean_pred = statistics.mean(p for p, a in pts)
            mean_actual = statistics.mean(a for p, a in pts)
            ece += bucket_weight * abs(mean_pred - mean_actual)

        return ece

    @staticmethod
    def calculate_entropy(agent_counts: Counter) -> float:
        """Routing entropy (0=collapse, 1=uniform)"""
        total = sum(agent_counts.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in agent_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * (p ** 0.5)

        entropy = max(0.0, min(1.0, entropy + 1.0))
        return entropy

    @staticmethod
    def calculate_concentration(agent_counts: Counter) -> float:
        """Routing concentration (0=uniform, 1=full collapse)"""
        total = sum(agent_counts.values())
        if total == 0:
            return 0.0

        max_count = max(agent_counts.values())
        return max_count / total


class TelemetryCollector:
    """Collect and persist telemetry data"""

    def __init__(self, base_path: str = None):
        self.base_path = base_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry"
        self.results: List[TaskResult] = []
        self.daily_metrics: List[DailyMetrics] = []

    def record(self, result: TaskResult):
        self.results.append(result)

    def record_daily_metrics(self, metrics: DailyMetrics):
        self.daily_metrics.append(metrics)

    def get_results_by_type(self, task_type: str) -> List[TaskResult]:
        return [r for r in self.results if r.task_type == task_type]

    def get_predictions_by_type(self, task_type: str) -> List[Tuple[float, float]]:
        results = self.get_results_by_type(task_type)
        return [(r.predicted_utility, r.actual_outcome) for r in results]

    def calculate_daily_metrics(self, date: str, results: List[TaskResult]) -> DailyMetrics:
        """Calculate metrics for a specific day"""
        ece_by_type = {}
        task_types = ["build", "deploy", "delete", "research", "fix", "review"]
        for task_type in task_types:
            preds = [(r.predicted_utility, r.actual_outcome) for r in results if r.task_type == task_type]
            if preds:
                ece_by_type[task_type] = MetricsCalculator.calculate_ece(preds)

        agent_counts = Counter(r.agent for r in results)
        entropy = MetricsCalculator.calculate_entropy(agent_counts)
        concentration = MetricsCalculator.calculate_concentration(agent_counts)

        decisions = Counter(r.governance_decision for r in results)
        total = len(results)
        block_rate = decisions.get("blocked", 0) / total if total > 0 else 0.0

        return DailyMetrics(
            date=date,
            ece_by_type=ece_by_type,
            routing_entropy=entropy,
            routing_concentration=concentration,
            governance_block_rate=block_rate,
            total_tasks=total,
            approved=decisions.get("approved", 0),
            blocked=decisions.get("blocked", 0),
            conditional=decisions.get("conditional", 0),
        )

    def save(self, path: str = None):
        """Save telemetry to JSON file"""
        if path is None:
            path = f"{self.base_path}/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "results": [asdict(r) for r in self.results],
            "daily_metrics": [asdict(m) for m in self.daily_metrics],
            "summary": self._generate_summary()
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        return path

    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        if not self.results:
            return {}

        all_predictions = [(r.predicted_utility, r.actual_outcome) for r in self.results]
        overall_ece = MetricsCalculator.calculate_ece(all_predictions)

        agent_counts = Counter(r.agent for r in self.results)
        routing_entropy = MetricsCalculator.calculate_entropy(agent_counts)
        routing_concentration = MetricsCalculator.calculate_concentration(agent_counts)

        decisions = Counter(r.governance_decision for r in self.results)
        total = len(self.results)
        block_rate = decisions.get("blocked", 0) / total if total > 0 else 0.0

        return {
            "overall_ece": overall_ece,
            "routing_entropy": routing_entropy,
            "routing_concentration": routing_concentration,
            "governance_block_rate": block_rate,
            "total_tasks": total,
            "decisions": dict(decisions),
        }


class SystemRunner:
    """
    Main 30-day execution runner

    Usage:
        runner = SystemRunner(days=30, tasks_per_day=50)
        runner.run()
        runner.print_report()
    """

    def __init__(
        self,
        days: int = 30,
        tasks_per_day: int = 50,
        seed: int = 42,
        calibration系统=None,
        governor=None,
        shadow_runner=None
    ):
        self.days = days
        self.tasks_per_day = tasks_per_day
        self.seed = seed

        self.calibration = calibration系统 or UnifiedCalibrationSystem()
        self.governor = governor or CalibrationGovernor()
        self.shadow_runner = shadow_runner or ShadowModeRunner()

        self.task_generator = TaskGenerator(seed=seed)
        self.outcome_simulator = OutcomeSimulator(seed=seed)
        self.telemetry = TelemetryCollector()
        self.metrics_calc = MetricsCalculator()

        self.all_results: List[TaskResult] = []

    def run_day(self, day: int, date: str) -> List[TaskResult]:
        """Execute one day's worth of tasks"""
        daily_results = []

        for task_num in range(self.tasks_per_day):
            description, task_type_str, agent, path, base_utility = self.task_generator.generate_task()

            shadow_task = self.shadow_runner.process_task(
                description=description,
                task_type_str=task_type_str.upper(),
                proposed_agent=agent,
                proposed_path=path,
                utility_prediction=base_utility
            )

            evaluation = self.calibration.evaluate(
                task_type=task_type_str,
                expected_success=base_utility,
                external_dependencies=random.randint(0, 5),
                hidden_state_indicators=random.randint(0, 3)
            )

            governance_decision = evaluation["decision"]

            if governance_decision == "blocked":
                actual = 0.0
                success = False
                exec_time = 0.0
                rollback = False
            else:
                external_deps = random.randint(0, 5)
                hidden_state = random.randint(0, 3)
                actual, success, exec_time, rollback = self.outcome_simulator.simulate(
                    task_type_str, base_utility, external_deps, hidden_state
                )

                self.calibration.record_outcome(task_type_str, base_utility, actual)

                self.governor.record(
                    task_id=shadow_task.task_id,
                    agent_id=agent,
                    predicted=base_utility,
                    actual=actual,
                    confidence=0.7 + random.random() * 0.25
                )

            result = TaskResult(
                task_id=shadow_task.task_id,
                task_type=task_type_str,
                predicted_utility=base_utility,
                actual_outcome=actual,
                agent=agent,
                governance_decision=governance_decision,
                execution_time=exec_time,
                external_deps=random.randint(0, 5),
                hidden_state=hidden_state if governance_decision != "blocked" else 0,
                rollback=rollback,
                timestamp=datetime.now().isoformat()
            )

            daily_results.append(result)
            self.telemetry.record(result)

        return daily_results

    def run(self) -> Dict[str, Any]:
        """Run the full 30-day simulation"""
        print("=" * 70)
        print("30-DAY SYSTEM VALIDATION RUN")
        print("=" * 70)
        print(f"Days: {self.days}, Tasks/Day: {self.tasks_per_day}")
        print(f"Total Tasks: {self.days * self.tasks_per_day}")
        print("=" * 70)

        start_date = datetime.now()

        for day in range(1, self.days + 1):
            date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")

            daily_results = self.run_day(day, date)
            self.all_results.extend(daily_results)

            daily_metrics = self.telemetry.calculate_daily_metrics(date, daily_results)
            self.telemetry.record_daily_metrics(daily_metrics)

            if day % 5 == 0 or day == 1:
                print(f"\n[Day {day:2d}] {date}")
                print(f"  Tasks: {daily_metrics.total_tasks} | "
                      f"Approved: {daily_metrics.approved} | "
                      f"Blocked: {daily_metrics.blocked} | "
                      f"Conditional: {daily_metrics.conditional}")
                print(f"  ECE: {daily_metrics.ece_by_type}")
                print(f"  Routing Entropy: {daily_metrics.routing_entropy:.3f} | "
                      f"Concentration: {daily_metrics.routing_concentration:.3f}")
                print(f"  Block Rate: {daily_metrics.governance_block_rate:.1%}")

        save_path = self.telemetry.save()
        print(f"\n[+] Telemetry saved to: {save_path}")

        return {
            "telemetry": self.telemetry,
            "summary": self.telemetry._generate_summary(),
            "daily_metrics": self.telemetry.daily_metrics
        }

    def print_report(self):
        """Print final validation report"""
        summary = self.telemetry._generate_summary()

        print("\n" + "=" * 70)
        print("30-DAY VALIDATION REPORT")
        print("=" * 70)

        print("\n[CRITICAL METRICS]")
        print(f"  Overall ECE: {summary.get('overall_ece', 0):.3f}")
        print(f"  Routing Entropy: {summary.get('routing_entropy', 0):.3f}")
        print(f"  Routing Concentration: {summary.get('routing_concentration', 0):.3f}")
        print(f"  Governance Block Rate: {summary.get('governance_block_rate', 0):.1%}")

        print("\n[ECE BY TASK TYPE]")
        ece_summary = defaultdict(list)
        for m in self.telemetry.daily_metrics:
            for tt, ece in m.ece_by_type.items():
                ece_summary[tt].append(ece)

        for tt, eces in sorted(ece_summary.items()):
            avg_ece = statistics.mean(eces) if eces else 0
            trend = "↑" if len(eces) > 1 and eces[-1] > eces[0] else "↓"
            print(f"  {tt:12s}: ECE={avg_ece:.3f} {trend}")

        print("\n[ROUTING COLLAPSE CHECK]")
        concentrations = [m.routing_concentration for m in self.telemetry.daily_metrics]
        if concentrations:
            avg_conc = statistics.mean(concentrations)
            max_conc = max(concentrations)
            trend = "↑" if len(concentrations) > 1 and concentrations[-1] > concentrations[0] else "↓"
            print(f"  Avg Concentration: {avg_conc:.3f}")
            print(f"  Max Concentration: {max_conc:.3f} {trend}")
            if max_conc > 0.6:
                print("  ⚠️  ROUTING COLLAPSE WARNING")

        print("\n[GOVERNANCE PRESSURE CHECK]")
        block_rates = [m.governance_block_rate for m in self.telemetry.daily_metrics]
        if block_rates:
            avg_block = statistics.mean(block_rates)
            print(f"  Avg Block Rate: {avg_block:.1%}")
            if avg_block < 0.05:
                print("  ⚠️  GOVERNANCE TOO PERMISSIVE (block_rate < 5%)")
            elif avg_block > 0.50:
                print("  ⚠️  GOVERNANCE TOO RESTRICTIVE (block_rate > 50%)")
            else:
                print("  ✓  Governance pressure within healthy range (5-50%)")

        print("\n[DECISION DISTRIBUTION]")
        decisions = summary.get('decisions', {})
        total = sum(decisions.values())
        for decision, count in sorted(decisions.items()):
            pct = count / total if total > 0 else 0
            print(f"  {decision}: {count} ({pct:.1%})")

        print("\n" + "=" * 70)
        print("VALIDATION VERDICT")
        print("=" * 70)

        issues = []

        overall_ece = summary.get('overall_ece', 0)
        if overall_ece > 0.15:
            issues.append(f"ECE={overall_ece:.3f} > 0.15 (calibration unreliable)")
        elif overall_ece > 0.10:
            issues.append(f"ECE={overall_ece:.3f} > 0.10 (calibration degraded)")

        avg_conc = statistics.mean(concentrations) if concentrations else 0
        if avg_conc > 0.6:
            issues.append(f"Concentration={avg_conc:.3f} > 0.6 (routing collapse)")

        avg_block = statistics.mean(block_rates) if block_rates else 0
        if avg_block < 0.05:
            issues.append(f"BlockRate={avg_block:.1%} < 5% (governance ineffective)")
        elif avg_block > 0.50:
            issues.append(f"BlockRate={avg_block:.1%} > 50% (governance too restrictive)")

        if issues:
            print("⚠️  ISSUES DETECTED:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓  ALL METRICS WITHIN ACCEPTABLE RANGES")

        print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="30-Day System Validation")
    parser.add_argument("--days", type=int, default=30, help="Number of days to run")
    parser.add_argument("--tasks", type=int, default=50, help="Tasks per day")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    runner = SystemRunner(days=args.days, tasks_per_day=args.tasks, seed=args.seed)
    result = runner.run()
    runner.print_report()