#!/usr/bin/env python3
"""
Truth Dashboard - 可视化 Truth Metrics
读取 timeline 数据，生成实时健康度报告

用法：
python3 truth_dashboard.py
python3 truth_dashboard.py --date 2026-05-15
python3 truth_dashboard.py --summary
"""
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')

from infrastructure.tools.timeline_store import TimelineStore
from infrastructure.tools.truth_metrics import TruthValidator
from infrastructure.tools.orchestrator_audit import OrchestratorAudit
from infrastructure.tools.stability_audit import StabilityAudit


class TruthDashboard:
    """
    Truth Dashboard - 读取 timeline，生成健康度报告
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure/tools/timeline"
        self.store = TimelineStore(base_path=self.base_path)
    
    def load_events(self, date: str = None) -> List[Dict]:
        """加载指定日期的事件"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self.store.get_events_by_date(date)
    
    def generate_health_report(self, date: str = None) -> Dict[str, Any]:
        """生成健康度报告"""
        events = self.load_events(date)
        
        # 初始化验证器
        truth_validator = TruthValidator()
        orchestrator_audit = OrchestratorAudit()
        stability_audit = StabilityAudit()
        
        # 分类处理事件
        routing_events = []
        utility_events = []
        governance_events = []
        execution_events = []
        
        for e in events:
            event_type = e.get('event_type', '')
            if event_type == 'routing':
                routing_events.append(e)
            elif event_type == 'utility_eval':
                utility_events.append(e)
            elif event_type == 'governance_decision':
                governance_events.append(e)
            elif event_type == 'execution_path':
                execution_events.append(e)
        
        # 填充 Truth Metrics
        for e in utility_events:
            task_id = e.get('action_id', '')
            agent_id = e.get('agent_id', '')
            expected = e.get('utility_output', 0.0)
            if expected > 0:
                # 预测 = 结果（简化，实际应该分开记录预测和结果）
                truth_validator.record_utility_prediction(
                    task_id, agent_id, expected,
                    e.get('utility_input', []),
                    e.get('metadata', {})
                )
        
        for e in routing_events:
            truth_validator.record_routing(
                e.get('action_id', ''),
                e.get('agent_id', ''),
                e.get('context', ''),
                e.get('available_agents', []),
                e.get('reasoning', '')
            )
            orchestrator_audit.record_routing(
                e.get('action_id', ''),
                e.get('agent_id', '')
            )
            orchestrator_audit.record_usage(e.get('agent_id', ''))
        
        for e in governance_events:
            truth_validator.record_governance(
                e.get('action_id', ''),
                e.get('proposed_action', ''),
                e.get('decision', ''),
                e.get('constraints_checked', []),
                e.get('reason', ''),
                e.get('actual_outcome')
            )
        
        for e in execution_events:
            path = e.get('execution_path', [])
            if path:
                stability_audit.record_routing(path)
        
        # 生成报告
        truth_report = truth_validator.run_validation()
        orchestrator_report = orchestrator_audit.run_audit()
        stability_report = stability_audit.run_audit()
        
        return {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_events': len(events),
            'routing_events': len(routing_events),
            'utility_events': len(utility_events),
            'governance_events': len(governance_events),
            'execution_events': len(execution_events),
            'truth': truth_report,
            'orchestrator': orchestrator_report,
            'stability': stability_report,
        }
    
    def print_dashboard(self, date: str = None):
        """打印 Dashboard 报告"""
        print("=" * 70)
        print("TRUTH DASHBOARD")
        print("=" * 70)
        
        report = self.generate_health_report(date)
        
        print(f"\n日期: {report['date']}")
        print(f"总事件数: {report['total_events']}")
        print(f"  - Routing: {report['routing_events']}")
        print(f"  - Utility: {report['utility_events']}")
        print(f"  - Governance: {report['governance_events']}")
        print(f"  - Execution: {report['execution_events']}")
        
        # Truth Score
        truth = report['truth']
        print(f"\n{'='*70}")
        print("TRUTH SCORE")
        print(f"{'='*70}")
        score = truth.overall_truth_score
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        status = "✓ HEALTHY" if score > 0.7 else "⚠ WARNING" if score > 0.5 else "✗ CRITICAL"
        print(f"[{bar}] {score:.1%} {status}")
        
        # Utility
        print(f"\n--- Utility Truth ---")
        print(f"  Honesty Score:    {truth.utility.honesty_score:.1%}")
        print(f"  Mean Delta:       {truth.utility.mean_delta:+.3f}")
        print(f"  Collapse Risk:    {truth.utility.collapse_risk:.1%}")
        print(f"  Reward Hack Risk: {truth.utility.reward_hack_risk:.1%}")
        for issue in truth.utility.issues:
            print(f"  ! {issue}")
        
        # Routing
        print(f"\n--- Routing Truth ---")
        print(f"  Consistency:      {truth.routing.consistency_rate:.1%}")
        print(f"  Entropy:          {truth.routing.agent_selection_entropy:.2f}")
        print(f"  Redundancy:       {truth.routing.redundancy_score:.1%}")
        for issue in truth.routing.issues:
            print(f"  ! {issue}")
        
        # Governance
        print(f"\n--- Governance Truth ---")
        print(f"  False Positive:   {truth.governance.false_positive_rate:.1%}")
        print(f"  False Negative:   {truth.governance.false_negative_rate:.1%}")
        print(f"  Accuracy:         {truth.governance.accuracy:.1%}")
        for issue in truth.governance.issues:
            print(f"  ! {issue}")
        
        # Critical Issues
        if truth.critical_issues:
            print(f"\n{'='*70}")
            print("CRITICAL ISSUES")
            print(f"{'='*70}")
            for issue in truth.critical_issues:
                print(f"  ! {issue}")
        
        # Recommendations
        if truth.recommendations:
            print(f"\n{'='*70}")
            print("RECOMMENDATIONS")
            print(f"{'='*70}")
            for rec in truth.recommendations:
                print(f"  → {rec}")
        
        # System Health Summary
        print(f"\n{'='*70}")
        print("SYSTEM HEALTH SUMMARY")
        print(f"{'='*70}")
        print(f"  Orchestrator: {report['orchestrator'].severity}")
        print(f"  Stability:   {report['stability'].severity}")
        
        print(f"\n{'='*70}")
        print(f"Generated: {datetime.now().isoformat()}")
        print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description='Truth Dashboard')
    parser.add_argument('--date', type=str, default=None, help='Date (YYYY-MM-DD)')
    parser.add_argument('--summary', action='store_true', help='Short summary only')
    args = parser.parse_args()
    
    dashboard = TruthDashboard()
    
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime('%Y-%m-%d')
    
    if args.summary:
        # 简短报告
        report = dashboard.generate_health_report(date)
        truth = report['truth']
        score = truth.overall_truth_score
        status = "✓" if score > 0.7 else "⚠" if score > 0.5 else "✗"
        print(f"{status} {date}: Truth Score {score:.1%} | Events: {report['total_events']}")
    else:
        dashboard.print_dashboard(date)


if __name__ == "__main__":
    main()
