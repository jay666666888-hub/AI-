#!/usr/bin/env python3
"""
Routing Truth Analyzer - Observer Layer
不参与决策，只验证 orchestrator 是否"说真话"

核心职责：
① Routing Consistency Score - 同一 task 是否 routing 一致
② Agent Redundancy Map - 功能重叠检测
③ Dependency Validity Score - dependency 是否真的影响 execution
"""

import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


@dataclass
class RoutingConsistencyResult:
    is_consistent: bool
    entropy_score: float
    routing_stability: float
    task_agent_mapping: Dict[str, Dict[str, int]]
    issues: List[str]


@dataclass
class RedundancyMapResult:
    is_effective: bool
    overlap_matrix: Dict[str, Dict[str, float]]
    high_overlap_pairs: List[Tuple[str, str, float]]
    usage_distribution_skew: float
    redundant_agents: List[str]
    issues: List[str]


@dataclass
class DependencyValidityResult:
    is_effective: bool
    dependency_coverage: float
    unused_dependencies: List[str]
    graph_depth: int
    issues: List[str]


@dataclass
class OrchestratorAuditReport:
    timestamp: str
    routing: RoutingConsistencyResult
    redundancy: RedundancyMapResult
    dependency: DependencyValidityResult
    overall_healthy: bool
    severity: str


class RoutingAnalyzer:
    def __init__(self):
        self.task_routing_history: List[Tuple[str, str, str]] = []
        self.task_agent_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def record_routing(self, task: str, agent: str, context: str = ""):
        self.task_routing_history.append((task, agent, datetime.now().isoformat()))
        self.task_agent_counts[task][agent] += 1

    def compute_entropy_score(self) -> float:
        if not self.task_agent_counts:
            return 0.0
        total_entropy = 0.0
        total_samples = 0
        for task, agent_counts in self.task_agent_counts.items():
            total = sum(agent_counts.values())
            if total < 2:
                continue
            entropy = 0.0
            for agent_count in agent_counts.values():
                p = agent_count / total
                if p > 0:
                    entropy -= p * (p ** 0.5)
            total_entropy += entropy
            total_samples += 1
        if total_samples == 0:
            return 0.0
        return min(1.0, total_entropy / total_samples)

    def compute_routing_stability(self) -> float:
        if not self.task_agent_counts:
            return 1.0
        stable_count = 0
        total_count = 0
        for task, agent_counts in self.task_agent_counts.items():
            total = sum(agent_counts.values())
            if total < 2:
                continue
            most_common_count = max(agent_counts.values())
            stable_count += most_common_count
            total_count += total
        if total_count == 0:
            return 1.0
        return stable_count / total_count

    def analyze(self) -> RoutingConsistencyResult:
        entropy = self.compute_entropy_score()
        stability = self.compute_routing_stability()
        issues = []
        if entropy > 0.7:
            issues.append(f"High routing entropy ({entropy:.2f}) - possible random routing")
        if stability < 0.6:
            issues.append(f"Low routing stability ({stability:.1%}) - inconsistent routing")
        is_consistent = len(issues) == 0
        return RoutingConsistencyResult(
            is_consistent=is_consistent,
            entropy_score=entropy,
            routing_stability=stability,
            task_agent_mapping=dict(self.task_agent_counts),
            issues=issues
        )


class AgentRedundancyAnalyzer:
    def __init__(self):
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_usage: Dict[str, int] = Counter()

    def register_agent(self, agent_id: str, capabilities: List[str]):
        self.agent_capabilities[agent_id] = set(capabilities)

    def record_usage(self, agent_id: str):
        self.agent_usage[agent_id] += 1

    def compute_overlap_matrix(self) -> Dict[str, Dict[str, float]]:
        overlap = {}
        agents = list(self.agent_capabilities.keys())
        for i, a in enumerate(agents):
            overlap[a] = {}
            a_caps = self.agent_capabilities[a]
            for j, b in enumerate(agents):
                if i == j:
                    overlap[a][b] = 1.0
                    continue
                b_caps = self.agent_capabilities[b]
                intersection = len(a_caps & b_caps)
                union = len(a_caps | b_caps)
                overlap[a][b] = intersection / union if union > 0 else 0.0
        return overlap

    def find_high_overlap_pairs(self, threshold=0.7) -> List[Tuple[str, str, float]]:
        pairs = []
        overlap = self.compute_overlap_matrix()
        agents = list(overlap.keys())
        for i, a in enumerate(agents):
            for j, b in enumerate(agents):
                if i >= j:
                    continue
                o = overlap[a][b]
                if o > threshold:
                    pairs.append((a, b, o))
        return sorted(pairs, key=lambda x: -x[2])

    def compute_usage_skew(self) -> float:
        if not self.agent_usage:
            return 0.0
        counts = list(self.agent_usage.values())
        total = sum(counts)
        if total == 0:
            return 0.0
        mean = total / len(counts)
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5
        if mean == 0:
            return 0.0
        gini = (2 * sum(i * c for i, c in enumerate(sorted(counts)))) / (len(counts) * total) - (len(counts) + 1) / len(counts)
        return max(0.0, min(1.0, gini))

    def analyze(self) -> RedundancyMapResult:
        high_overlap = self.find_high_overlap_pairs()
        skew = self.compute_usage_skew()
        issues = []
        redundant = []
        if high_overlap:
            issues.append(f"Found {len(high_overlap)} high-overlap agent pairs")
            redundant = list(set([a for a, b, _ in high_overlap] + [b for a, b, _ in high_overlap]))
        if skew > 0.8:
            issues.append(f"High usage distribution skew ({skew:.2f}) - some agents overused")
        is_effective = len(issues) == 0
        return RedundancyMapResult(
            is_effective=is_effective,
            overlap_matrix=self.compute_overlap_matrix(),
            high_overlap_pairs=high_overlap,
            usage_distribution_skew=skew,
            redundant_agents=redundant,
            issues=issues
        )


class DependencyAnalyzer:
    def __init__(self):
        self.execution_traces: List[Dict] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.dependency_usage: Dict[Tuple[str, str], int] = Counter()

    def register_dependency(self, from_node: str, to_node: str):
        self.dependency_graph[from_node].add(to_node)

    def record_execution(self, execution_path: List[str]):
        self.execution_traces.append({'path': execution_path, 'used_dependencies': []})
        for i, node in enumerate(execution_path):
            if i == 0:
                continue
            prev_node = execution_path[i - 1]
            if prev_node in self.dependency_graph:
                deps = self.dependency_graph[prev_node]
                if node in deps:
                    self.dependency_usage[(prev_node, node)] += 1

    def compute_dependency_coverage(self) -> float:
        if not self.dependency_graph:
            return 0.0
        total_deps = sum(len(deps) for deps in self.dependency_graph.values())
        used_deps = sum(1 for (d, _) in self.dependency_usage.keys() if self.dependency_usage[(d, _)] > 0)
        return used_deps / total_deps if total_deps > 0 else 0.0

    def find_unused_dependencies(self) -> List[str]:
        unused = []
        for from_node, to_nodes in self.dependency_graph.items():
            for to_node in to_nodes:
                if self.dependency_usage[(from_node, to_node)] == 0:
                    unused.append(f"{from_node} -> {to_node}")
        return unused

    def compute_graph_depth(self) -> int:
        if not self.execution_traces:
            return 0
        return max(len(trace['path']) for trace in self.execution_traces)

    def analyze(self) -> DependencyValidityResult:
        coverage = self.compute_dependency_coverage()
        unused = self.find_unused_dependencies()
        depth = self.compute_graph_depth()
        issues = []
        if coverage < 0.5:
            issues.append(f"Low dependency coverage ({coverage:.1%}) - graph not used")
        if len(unused) > 5:
            issues.append(f"Many unused dependencies ({len(unused)}) - possible decorative graph")
        is_effective = len(issues) == 0 and coverage > 0.7
        return DependencyValidityResult(
            is_effective=is_effective,
            dependency_coverage=coverage,
            unused_dependencies=unused[:10],
            graph_depth=depth,
            issues=issues
        )


class OrchestratorAudit:
    def __init__(self):
        self.routing_analyzer = RoutingAnalyzer()
        self.redundancy_analyzer = AgentRedundancyAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.audit_start = datetime.now().isoformat()

    def record_routing(self, task: str, agent: str):
        self.routing_analyzer.record_routing(task, agent)

    def register_agent(self, agent_id: str, capabilities: List[str]):
        self.redundancy_analyzer.register_agent(agent_id, capabilities)

    def record_usage(self, agent_id: str):
        self.redundancy_analyzer.record_usage(agent_id)

    def register_dependency(self, from_node: str, to_node: str):
        self.dependency_analyzer.register_dependency(from_node, to_node)

    def record_execution(self, execution_path: List[str]):
        self.dependency_analyzer.record_execution(execution_path)

    def run_audit(self) -> OrchestratorAuditReport:
        routing_result = self.routing_analyzer.analyze()
        redundancy_result = self.redundancy_analyzer.analyze()
        dependency_result = self.dependency_analyzer.analyze()
        all_healthy = routing_result.is_consistent and redundancy_result.is_effective and dependency_result.is_effective
        severity = "OK"
        if not all_healthy:
            severity = "CRITICAL" if not routing_result.is_consistent else "WARNING"
        return OrchestratorAuditReport(
            timestamp=self.audit_start,
            routing=routing_result,
            redundancy=redundancy_result,
            dependency=dependency_result,
            overall_healthy=all_healthy,
            severity=severity
        )

    def generate_report(self) -> str:
        report = self.run_audit()
        lines = [
            "=" * 60,
            "ROUTING TRUTH ANALYZER - Audit Report",
            "=" * 60,
            f"Timestamp: {report.timestamp}",
            f"Overall Status: {report.severity}",
            "",
            "【① Routing Consistency Score】",
            f"  Consistent: {report.routing.is_consistent}",
            f"  Entropy Score: {report.routing.entropy_score:.3f}",
            f"  Stability: {report.routing.routing_stability:.1%}",
        ]
        if report.routing.issues:
            for issue in report.routing.issues:
                lines.append(f"  ! {issue}")
        else:
            lines.append("  OK - No issues")
        lines.extend([
            "",
            "【② Agent Redundancy Map】",
            f"  Effective: {report.redundancy.is_effective}",
            f"  High Overlap Pairs: {len(report.redundancy.high_overlap_pairs)}",
            f"  Usage Skew: {report.redundancy.usage_distribution_skew:.3f}",
            f"  Redundant Agents: {len(report.redundancy.redundant_agents)}",
        ])
        if report.redundancy.issues:
            for issue in report.redundancy.issues:
                lines.append(f"  ! {issue}")
        else:
            lines.append("  OK - No issues")
        lines.extend([
            "",
            "【③ Dependency Validity Score】",
            f"  Effective: {report.dependency.is_effective}",
            f"  Coverage: {report.dependency.dependency_coverage:.1%}",
            f"  Graph Depth: {report.dependency.graph_depth}",
            f"  Unused Deps: {len(report.dependency.unused_dependencies)}",
        ])
        if report.dependency.issues:
            for issue in report.dependency.issues:
                lines.append(f"  ! {issue}")
        else:
            lines.append("  OK - No issues")
        lines.extend(["", "=" * 60, f"Final Verdict: {report.severity}", "=" * 60])
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("Routing Truth Analyzer - Starting Audit")
    print("=" * 60)
    audit = OrchestratorAudit()
    print("\n[1] Registering agents...")
    audit.register_agent("planner", ["plan", "design", "coordinate"])
    audit.register_agent("coder", ["write", "refactor", "debug"])
    audit.register_agent("reviewer", ["review", "analyze", "suggest"])
    audit.register_agent("tester", ["test", "validate", "verify"])
    print("    4 agents registered")
    print("\n[2] Simulating routing...")
    tasks = ["build_feature", "fix_bug", "write_test", "review_code", "deploy"]
    import random
    for task in tasks * 10:
        agents = ["planner", "coder", "reviewer", "tester"]
        agent = random.choice(agents) if random.random() > 0.6 else "coder"
        audit.record_routing(task, agent)
        audit.record_usage(agent)
    print("\n[3] Simulating dependencies...")
    audit.register_dependency("planner", "coder")
    audit.register_dependency("coder", "reviewer")
    audit.register_dependency("reviewer", "tester")
    audit.register_dependency("tester", "deployer")
    print("\n[4] Simulating execution...")
    for _ in range(20):
        path = ["planner", "coder", "reviewer", "tester"]
        random.shuffle(path)
        audit.record_execution(path[:random.randint(2, 4)])
    print("\n[5] Running audit...")
    report = audit.run_audit()
    print(f"\n[6] Results:")
    print(f"    Overall: {report.severity}")
    print(f"    Routing Consistent: {report.routing.is_consistent}")
    print(f"    Agent Effective: {report.redundancy.is_effective}")
    print(f"    Dependency Effective: {report.dependency.is_effective}")
    print("\n" + audit.generate_report())
