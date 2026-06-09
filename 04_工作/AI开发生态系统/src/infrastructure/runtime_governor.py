#!/usr/bin/env python3
"""
Runtime Governor Layer - 运行时Governor层
统一决策点 + 硬约束引擎 + 执行门控

所有系统必须经过: Governor.validate(action)

包含:
1. Hard Constraint Engine - 硬性约束引擎
2. Execution Gate - 执行门控 (ALLOW/BLOCK/DEGRADE/ROLLBACK)
3. Transaction Hook - 事务挂钩
4. Unified Decision Point - 统一决策入口
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class GateDecision(Enum):
    """执行门决策"""
    ALLOW = "allow"           # 完全放行
    BLOCK = "block"           # 完全阻止
    DEGRADE = "degrade"       # 降级执行 (简化路径)
    ROLLBACK = "rollback"     # 回滚


class ConstraintType(Enum):
    """约束类型"""
    UTILITY_THRESHOLD = "utility_threshold"
    FAILURE_RATE = "failure_rate"
    RESOURCE_LIMIT = "resource_limit"
    TIME_LIMIT = "time_limit"
    DEPENDENCY_VIOLATION = "dependency_violation"
    RECURSION_DEPTH = "recursion_depth"
    POLICY_DRIFT = "policy_drift"


@dataclass
class HardConstraint:
    """硬性约束"""
    constraint_type: ConstraintType
    threshold: float
    severity: str  # "critical", "high", "medium"
    action_on_violation: GateDecision
    description: str


@dataclass
class ConstraintViolation:
    """约束违规"""
    constraint_type: ConstraintType
    current_value: float
    threshold: float
    severity: str
    timestamp: str
    action_taken: GateDecision
    context: Dict[str, Any]


@dataclass
class ExecutionContext:
    """执行上下文"""
    action_id: str
    action_type: str
    proposed_at: str
    deadline_ms: Optional[int]
    resource_budget: Dict[str, float]
    dependencies: List[str]
    retry_count: int
    recursion_depth: int


@dataclass
class GovernorDecision:
    """Governor决策"""
    decision_id: str
    action_id: str
    decision: GateDecision
    constraints_checked: List[ConstraintType]
    violations: List[ConstraintViolation]
    utility_score: float
    reasoning: str
    timestamp: str
    metadata: Dict[str, Any]


class HardConstraintEngine:
    """
    Hard Constraint Engine - 硬性约束引擎
    
    定义并执行所有硬约束
    """
    
    def __init__(self):
        self.constraints: List[HardConstraint] = []
        self._setup_default_constraints()
    
    def _setup_default_constraints(self):
        """设置默认硬约束"""
        self.constraints = [
            # Utility 约束
            HardConstraint(
                constraint_type=ConstraintType.UTILITY_THRESHOLD,
                threshold=0.2,  # utility < 0.2 = 危险
                severity="critical",
                action_on_violation=GateDecision.BLOCK,
                description="Utility低于20%立即阻止"
            ),
            
            # 失败率约束
            HardConstraint(
                constraint_type=ConstraintType.FAILURE_RATE,
                threshold=0.3,  # 失败率 > 30% = 危险
                severity="critical",
                action_on_violation=GateDecision.ROLLBACK,
                description="失败率超过30%触发回滚"
            ),
            
            # 资源限制
            HardConstraint(
                constraint_type=ConstraintType.RESOURCE_LIMIT,
                threshold=0.9,  # 资源使用 > 90% = 危险
                severity="high",
                action_on_violation=GateDecision.DEGRADE,
                description="资源使用超过90%降级执行"
            ),
            
            # 时间限制
            HardConstraint(
                constraint_type=ConstraintType.TIME_LIMIT,
                threshold=60000,  # 60秒超时
                severity="high",
                action_on_violation=GateDecision.DEGRADE,
                description="执行超过60秒降级路径"
            ),
            
            # 依赖违规
            HardConstraint(
                constraint_type=ConstraintType.DEPENDENCY_VIOLATION,
                threshold=0.0,  # 任何依赖违规 = 阻止
                severity="critical",
                action_on_violation=GateDecision.BLOCK,
                description="依赖未满足立即阻止"
            ),
            
            # 递归深度
            HardConstraint(
                constraint_type=ConstraintType.RECURSION_DEPTH,
                threshold=5.0,  # 递归 > 5 = 危险
                severity="high",
                action_on_violation=GateDecision.BLOCK,
                description="递归深度超过5阻止"
            ),
            
            # Policy Drift
            HardConstraint(
                constraint_type=ConstraintType.POLICY_DRIFT,
                threshold=0.15,  # 漂移 > 15% = 危险
                severity="high",
                action_on_violation=GateDecision.DEGRADE,
                description="策略漂移超过15%降级执行"
            ),
        ]
    
    def check_constraint(self,
                        constraint_type: ConstraintType,
                        current_value: float) -> tuple[bool, HardConstraint]:
        """
        检查约束
        
        Returns:
            (is_violated, constraint)
        """
        constraint = next(
            (c for c in self.constraints if c.constraint_type == constraint_type),
            None
        )
        
        if not constraint:
            return False, None
        
        # 根据约束类型比较
        if constraint_type in [ConstraintType.UTILITY_THRESHOLD,
                              ConstraintType.FAILURE_RATE,
                              ConstraintType.RECURSION_DEPTH,
                              ConstraintType.POLICY_DRIFT]:
            is_violated = current_value < constraint.threshold
        else:
            is_violated = current_value > constraint.threshold
        
        return is_violated, constraint
    
    def check_all(self, metrics: Dict[str, float]) -> List[ConstraintViolation]:
        """
        检查所有约束
        
        Args:
            metrics: {constraint_type: current_value}
        """
        violations = []
        
        for constraint in self.constraints:
            ct = constraint.constraint_type
            if ct.value in metrics:
                is_violated, _ = self.check_constraint(ct, metrics[ct.value])
                
                if is_violated:
                    violations.append(ConstraintViolation(
                        constraint_type=ct,
                        current_value=metrics[ct.value],
                        threshold=constraint.threshold,
                        severity=constraint.severity,
                        timestamp=datetime.now().isoformat(),
                        action_taken=constraint.action_on_violation,
                        context={}
                    ))
        
        return violations
    
    def get_critical_violations(self, violations: List[ConstraintViolation]) -> List[ConstraintViolation]:
        """获取严重违规"""
        return [v for v in violations if v.severity == "critical"]


class TransactionHook:
    """
    Transaction Hook - 事务挂钩
    
    on_fail → auto rollback
    on_partial → checkpoint save
    on_risk → downgrade execution path
    """
    
    def __init__(self, transaction_manager=None, state_manager=None):
        self.transaction_manager = transaction_manager
        self.state_manager = state_manager
        
        self.hooks: Dict[str, Callable] = {
            "on_fail": self._hook_on_fail,
            "on_partial": self._hook_on_partial,
            "on_risk": self._hook_on_risk,
        }
    
    def trigger(self, event_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """触发钩子"""
        hook = self.hooks.get(event_type)
        if not hook:
            return {"status": "no_hook", "event_type": event_type}
        
        return hook(context)
    
    def _hook_on_fail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """失败时的自动回滚"""
        results = {
            "event": "on_fail",
            "actions": []
        }
        
        # 1. 保存检查点
        if self.state_manager:
            checkpoint_id = self.state_manager.save_checkpoint(
                stage=context.get("stage", "unknown"),
                pipeline_position=context.get("position", 0),
                total_stages=context.get("total_stages", 1),
                state=context.get("state", {}),
                metadata={"triggered_by": "on_fail", "reason": context.get("reason")}
            )
            results["actions"].append({
                "type": "checkpoint",
                "id": checkpoint_id,
                "status": "saved"
            })
        
        # 2. 执行回滚
        if self.transaction_manager:
            try:
                self.transaction_manager.rollback()
                results["actions"].append({
                    "type": "rollback",
                    "status": "executed"
                })
            except Exception as e:
                results["actions"].append({
                    "type": "rollback",
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _hook_on_partial(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """部分成功时保存检查点"""
        results = {
            "event": "on_partial",
            "actions": []
        }
        
        # 保存检查点
        if self.state_manager:
            checkpoint_id = self.state_manager.save_checkpoint(
                stage=context.get("stage", "unknown"),
                pipeline_position=context.get("position", 0),
                total_stages=context.get("total_stages", 1),
                state=context.get("state", {}),
                metadata={
                    "triggered_by": "on_partial",
                    "partial_data": context.get("partial_data", {}),
                    "success_rate": context.get("success_rate", 0)
                }
            )
            results["actions"].append({
                "type": "checkpoint",
                "id": checkpoint_id,
                "status": "saved"
            })
        
        return results
    
    def _hook_on_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """风险时降级执行路径"""
        results = {
            "event": "on_risk",
            "actions": []
        }
        
        # 保存预风险检查点
        if self.state_manager:
            checkpoint_id = self.state_manager.save_checkpoint(
                stage=context.get("stage", "unknown"),
                pipeline_position=context.get("position", 0),
                total_stages=context.get("total_stages", 1),
                state=context.get("state", {}),
                metadata={
                    "triggered_by": "on_risk",
                    "risk_type": context.get("risk_type", "unknown")
                }
            )
            results["actions"].append({
                "type": "pre_risk_checkpoint",
                "id": checkpoint_id,
                "status": "saved"
            })
        
        # 返回降级建议
        results["degradation"] = {
            "recommended_path": context.get("recommended_path", "safe_path"),
            "skip_stages": context.get("skip_stages", []),
            "simplify_logic": True
        }
        
        return results


class ExecutionGate:
    """
    Execution Gate - 执行门控
    
    根据约束违规决定执行行为
    """
    
    def __init__(self, constraint_engine: HardConstraintEngine):
        self.constraint_engine = constraint_engine
    
    def evaluate(self, violations: List[ConstraintViolation], context: Dict[str, Any]) -> GateDecision:
        """
        评估违规并决定门控行为
        
        Returns:
            GateDecision
        """
        if not violations:
            return GateDecision.ALLOW
        
        # 检查是否有 critical 违规
        critical = [v for v in violations if v.severity == "critical"]
        
        if any(critical):
            # 找最严重的 action
            critical_actions = [v.action_taken for v in critical]
            
            if GateDecision.ROLLBACK in critical_actions:
                return GateDecision.ROLLBACK
            elif GateDecision.BLOCK in critical_actions:
                return GateDecision.BLOCK
            else:
                return GateDecision.DEGRADE
        
        # 只有 high/medium 违规 → 降级
        high_violations = [v for v in violations if v.severity == "high"]
        if any(high_violations):
            return GateDecision.DEGRADE
        
        # 低严重度 → 警告但放行
        return GateDecision.ALLOW
    
    def get_degradation_path(self, original_path: str, context: Dict[str, Any]) -> str:
        """
        获取降级后的执行路径
        
        Args:
            original_path: 原始执行路径
            context: 上下文信息
        
        Returns:
            降级后的路径
        """
        # 降级策略映射
        degradation_map = {
            "fast_path": "safe_path",
            "aggressive": "conservative",
            "parallel": "sequential",
            "full_feature": "minimal",
        }
        
        # 根据风险类型选择降级路径
        risk_type = context.get("risk_type", "")
        
        if "resource" in risk_type:
            return "lightweight_path"
        elif "time" in risk_type:
            return "timeout_protected_path"
        elif "utility" in risk_type:
            return "high_confidence_path"
        else:
            return degradation_map.get(original_path, "safe_path")


class RuntimeGovernor:
    """
    Runtime Governor - 运行时Governor主引擎
    
    统一决策点
    所有系统必须经过: Governor.validate(action)
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/governor"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 组件
        self.constraint_engine = HardConstraintEngine()
        self.execution_gate = ExecutionGate(self.constraint_engine)
        self.transaction_hook = TransactionHook()
        
        # 决策历史
        self.decisions: List[GovernorDecision] = []
        self.violations_history: List[ConstraintViolation] = []
        
        # 统计
        self.stats = {
            "total_validations": 0,
            "allow_count": 0,
            "block_count": 0,
            "degrade_count": 0,
            "rollback_count": 0
        }
        
        self._load_history()
    
    def _load_history(self):
        decisions_file = os.path.join(self.storage_path, "decisions.json")
        if os.path.exists(decisions_file):
            try:
                with open(decisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decisions = [GovernorDecision(**d) for d in data]
            except:
                self.decisions = []
        
        violations_file = os.path.join(self.storage_path, "violations.json")
        if os.path.exists(violations_file):
            try:
                with open(violations_file, 'r', encoding='utf-8') as f:
                    self.violations_history = [ConstraintViolation(**v) for v in json.load(f)]
            except:
                self.violations_history = []
    
    def _save_history(self):
        decisions_file = os.path.join(self.storage_path, "decisions.json")
        with open(decisions_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "decision_id": d.decision_id,
                "action_id": d.action_id,
                "decision": d.decision.value,
                "constraints_checked": [c.value for c in d.constraints_checked],
                "violations": [{
                    "constraint_type": v.constraint_type.value,
                    "current_value": v.current_value,
                    "threshold": v.threshold,
                    "severity": v.severity,
                    "timestamp": v.timestamp,
                    "action_taken": v.action_taken.value,
                    "context": v.context
                } for v in d.violations],
                "utility_score": d.utility_score,
                "reasoning": d.reasoning,
                "timestamp": d.timestamp,
                "metadata": d.metadata
            } for d in self.decisions[-100:]], f, ensure_ascii=False, indent=2)
        
        violations_file = os.path.join(self.storage_path, "violations.json")
        with open(violations_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "constraint_type": v.constraint_type.value,
                "current_value": v.current_value,
                "threshold": v.threshold,
                "severity": v.severity,
                "timestamp": v.timestamp,
                "action_taken": v.action_taken.value,
                "context": v.context
            } for v in self.violations_history[-100:]], f, ensure_ascii=False, indent=2)
    
    def validate(self,
                action_id: str,
                action_type: str,
                metrics: Dict[str, float],
                context: Dict[str, Any] = None) -> GovernorDecision:
        """
        统一验证入口
        
        所有系统必须经过此方法
        
        Args:
            action_id: 行动ID
            action_type: 行动类型
            metrics: 指标 {constraint_type: value}
            context: 上下文
        
        Returns:
            GovernorDecision
        """
        ctx = context or {}
        decision_id = f"gov_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 1. 检查所有约束
        violations = self.constraint_engine.check_all(metrics)
        
        # 2. 评估门控
        gate_decision = self.execution_gate.evaluate(violations, ctx)
        
        # 3. 触发事务钩子
        if gate_decision == GateDecision.ROLLBACK:
            self.transaction_hook.trigger("on_fail", {
                "stage": ctx.get("stage"),
                "position": ctx.get("position", 0),
                "total_stages": ctx.get("total_stages", 1),
                "state": ctx.get("state", {}),
                "reason": f"Governor triggered rollback: {[v.constraint_type.value for v in violations]}"
            })
        elif gate_decision == GateDecision.DEGRADE:
            # 检查是否需要降级路径
            self.transaction_hook.trigger("on_risk", {
                "stage": ctx.get("stage"),
                "position": ctx.get("position", 0),
                "total_stages": ctx.get("total_stages", 1),
                "state": ctx.get("state", {}),
                "risk_type": ctx.get("risk_type", "general"),
                "recommended_path": self.execution_gate.get_degradation_path(
                    ctx.get("current_path", "fast_path"), ctx
                )
            })
        
        # 4. 记录决策
        constraints_checked = [c.constraint_type for c in self.constraint_engine.constraints]
        
        reasoning = self._build_reasoning(gate_decision, violations)
        
        decision = GovernorDecision(
            decision_id=decision_id,
            action_id=action_id,
            decision=gate_decision,
            constraints_checked=constraints_checked,
            violations=violations,
            utility_score=metrics.get(ConstraintType.UTILITY_THRESHOLD.value, 1.0),
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
            metadata={
                "action_type": action_type,
                "context": ctx
            }
        )
        
        self.decisions.append(decision)
        self.violations_history.extend(violations)
        
        # 更新统计
        self.stats["total_validations"] += 1
        if gate_decision == GateDecision.ALLOW:
            self.stats["allow_count"] += 1
        elif gate_decision == GateDecision.BLOCK:
            self.stats["block_count"] += 1
        elif gate_decision == GateDecision.DEGRADE:
            self.stats["degrade_count"] += 1
        elif gate_decision == GateDecision.ROLLBACK:
            self.stats["rollback_count"] += 1
        
        self._save_history()
        
        return decision
    
    def _build_reasoning(self, decision: GateDecision, violations: List[ConstraintViolation]) -> str:
        """构建决策理由"""
        if decision == GateDecision.ALLOW:
            return "所有约束检查通过"
        
        if decision == GateDecision.BLOCK:
            critical = [v for v in violations if v.severity == "critical"]
            return f"严重违规阻止执行: {[v.constraint_type.value for v in critical]}"
        
        if decision == GateDecision.DEGRADE:
            return f"检测到 {[v.severity for v in violations]} 级别违规, 降级执行"
        
        if decision == GateDecision.ROLLBACK:
            return f"严重违规触发回滚: {[v.constraint_type.value for v in violations]}"
        
        return "未知决策"
    
    def validate_action(self,
                        action_id: str,
                        utility: float = 1.0,
                        failure_rate: float = 0.0,
                        resource_usage: float = 0.0,
                        execution_time_ms: int = 0,
                        recursion_depth: int = 0,
                        policy_drift: float = 0.0,
                        context: Dict[str, Any] = None) -> GovernorDecision:
        """
        便捷验证方法
        
        所有系统调用的标准入口
        """
        metrics = {
            ConstraintType.UTILITY_THRESHOLD.value: utility,
            ConstraintType.FAILURE_RATE.value: failure_rate,
            ConstraintType.RESOURCE_LIMIT.value: resource_usage,
            ConstraintType.TIME_LIMIT.value: float(execution_time_ms),
            ConstraintType.RECURSION_DEPTH.value: float(recursion_depth),
            ConstraintType.POLICY_DRIFT.value: policy_drift,
        }
        
        return self.validate(
            action_id=action_id,
            action_type=context.get("action_type", "unknown") if context else "unknown",
            metrics=metrics,
            context=context
        )
    
    def get_decision(self, action_id: str) -> Optional[GovernorDecision]:
        """获取某个action的决策"""
        return next((d for d in self.decisions if d.action_id == action_id), None)
    
    def get_recent_violations(self, limit: int = 20) -> List[ConstraintViolation]:
        """获取最近的违规"""
        return self.violations_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_validations"]
        
        return {
            "total_validations": total,
            "allow_rate": self.stats["allow_count"] / total if total > 0 else 0,
            "block_rate": self.stats["block_count"] / total if total > 0 else 0,
            "degrade_rate": self.stats["degrade_count"] / total if total > 0 else 0,
            "rollback_rate": self.stats["rollback_count"] / total if total > 0 else 0,
            "recent_violations_count": len(self.violations_history[-50:]),
            "critical_violations": len([v for v in self.violations_history if v.severity == "critical"])
        }
    
    def can_proceed(self, action_id: str) -> tuple[bool, str]:
        """
        快速检查是否可以继续
        
        Returns:
            (can_proceed, reason)
        """
        decision = self.get_decision(action_id)
        
        if not decision:
            return True, "无历史决策, 默认允许"
        
        if decision.decision == GateDecision.BLOCK:
            return False, f"被阻止: {decision.reasoning}"
        
        if decision.decision == GateDecision.ROLLBACK:
            return False, f"需要回滚: {decision.reasoning}"
        
        if decision.decision == GateDecision.DEGRADE:
            return True, f"降级执行: {decision.reasoning}"
        
        return True, "允许执行"


def create_runtime_governor() -> RuntimeGovernor:
    """工厂函数"""
    return RuntimeGovernor()


# 便捷函数
def validate_action(action_id: str,
                  utility: float = 1.0,
                  failure_rate: float = 0.0,
                  **kwargs) -> GovernorDecision:
    """快速验证action"""
    governor = create_runtime_governor()
    return governor.validate_action(action_id, utility, failure_rate, **kwargs)

__exports__ = ['ConstraintType', 'ConstraintViolation', 'ExecutionContext', 'ExecutionGate', 'GateDecision', 'GovernorDecision', 'HardConstraint', 'HardConstraintEngine', 'RuntimeGovernor', 'TransactionHook', 'create_runtime_governor', 'validate_action']


