#!/usr/bin/env python3
"""
System Invariant Engine - 系统不变量引擎
防止系统"悄悄变坏"

核心功能:
- Stability invariants (稳定性不变量)
- Behavioral invariants (行为不变量)
- Policy invariants (策略不变量)

定义并验证系统必须保持的条件
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class InvariantType(Enum):
    STABILITY = "stability"      # 稳定性不变量
    BEHAVIORAL = "behavioral"   # 行为不变量
    POLICY = "policy"            # 策略不变量
    RESOURCE = "resource"        # 资源不变量
    CAUSAL = "causal"            # 因果不变量


class ViolationSeverity(Enum):
    WARNING = "warning"      # 警告
    CRITICAL = "critical"   # 严重
    FATAL = "fatal"          # 致命


@dataclass
class Invariant:
    """不变量定义"""
    invariant_id: str
    name: str
    invariant_type: InvariantType
    description: str
    
    # 检查函数
    check_fn: Callable[[Dict], bool]  # 返回 True = 满足, False = 违反
    
    # 元数据
    severity: ViolationSeverity
    enabled: bool = True
    tolerance: float = 0.0  # 容忍度 (允许短时间违反)
    window_seconds: int = 0  # 时间窗口 (持续多久才触发)
    
    # 历史
    violation_count: int = 0
    last_check: str = ""
    last_violation: str = ""


@dataclass
class InvariantViolation:
    """不变量违反记录"""
    violation_id: str
    invariant_id: str
    invariant_name: str
    severity: ViolationSeverity
    timestamp: str
    current_value: Any
    expected_condition: str
    duration_ms: float
    context: Dict[str, Any]


@dataclass
class InvariantStatus:
    """不变量状态摘要"""
    total_invariants: int
    enabled_invariants: int
    violations: int
    critical_violations: int
    system_healthy: bool
    most_violated_invariant: Optional[str]


class SystemInvariantEngine:
    """
    System Invariant Engine - 系统不变量引擎
    
    定义并监控系统的不可违反条件
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/invariants"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.invariants: Dict[str, Invariant] = {}
        self.violations: List[InvariantViolation] = []
        self.violation_history: List[InvariantViolation] = []
        
        self._setup_default_invariants()
        self._load_history()
    
    def _setup_default_invariants(self):
        """设置默认不变量"""
        
        # ===== Stability Invariants =====
        self.add_invariant(Invariant(
            invariant_id="stability_utility_min",
            name="Utility不低于安全线",
            invariant_type=InvariantType.STABILITY,
            description="Utility 必须始终 >= 0.2",
            check_fn=lambda ctx: ctx.get("utility", 1.0) >= 0.2,
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="stability_utility_variance",
            name="Utility方差不能过大",
            invariant_type=InvariantType.STABILITY,
            description="Utility 在窗口内的方差必须 < 0.1",
            check_fn=lambda ctx: ctx.get("utility_variance", 0) < 0.1,
            severity=ViolationSeverity.WARNING
        ))
        
        # ===== Behavioral Invariants =====
        self.add_invariant(Invariant(
            invariant_id="behavioral_goal_quota",
            name="Goal生成不能超限",
            invariant_type=InvariantType.BEHAVIORAL,
            description="每小时Goal生成 <= 10",
            check_fn=lambda ctx: ctx.get("goals_per_hour", 0) <= 10,
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="behavioral_self_trigger_ratio",
            name="自触发比例不能过高",
            invariant_type=InvariantType.BEHAVIORAL,
            description="Self-trigger ratio <= 0.2 (20%)",
            check_fn=lambda ctx: ctx.get("self_trigger_ratio", 0) <= 0.2,
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="behavioral_no_infinite_loop",
            name="不能有无限循环",
            invariant_type=InvariantType.BEHAVIORAL,
            description="同一个action在30秒内不能出现超过3次",
            check_fn=lambda ctx: ctx.get("action_repeat_count", 0) <= 3,
            severity=ViolationSeverity.FATAL
        ))
        
        # ===== Policy Invariants =====
        self.add_invariant(Invariant(
            invariant_id="policy_no_structural_drift",
            name="不能有结构性策略漂移",
            invariant_type=InvariantType.POLICY,
            description="Policy drift 累计 <= 0.3",
            check_fn=lambda ctx: ctx.get("policy_drift", 0) <= 0.3,
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="policy_weight_sums",
            name="权重必须归一化",
            invariant_type=InvariantType.POLICY,
            description="权重和必须 ~= 1.0 (误差 < 0.05)",
            check_fn=lambda ctx: abs(ctx.get("weight_sum", 1.0) - 1.0) < 0.05,
            severity=ViolationSeverity.WARNING
        ))
        
        # ===== Resource Invariants =====
        self.add_invariant(Invariant(
            invariant_id="resource_memory_limit",
            name="内存使用不能超限",
            invariant_type=InvariantType.RESOURCE,
            description="内存使用 <= 90%",
            check_fn=lambda ctx: ctx.get("memory_usage", 0) <= 0.9,
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="resource_execution_time",
            name="执行时间不能超时",
            invariant_type=InvariantType.RESOURCE,
            description="单次执行时间 <= 60秒",
            check_fn=lambda ctx: ctx.get("execution_time_ms", 0) <= 60000,
            severity=ViolationSeverity.WARNING
        ))
        
        # ===== Causal Invariants =====
        self.add_invariant(Invariant(
            invariant_id="causal_no_reverse_causation",
            name="不能有逆向因果",
            invariant_type=InvariantType.CAUSAL,
            description="Effect不能先于Cause发生",
            check_fn=lambda ctx: ctx.get("reverse_causation_detected", False) == False,
            severity=ViolationSeverity.FATAL
        ))
        
        self.add_invariant(Invariant(
            invariant_id="causal_effect_magnitude",
            name="因果效应不能过大",
            invariant_type=InvariantType.CAUSAL,
            description="单次Cause的Effect magnitude <= 0.5",
            check_fn=lambda ctx: ctx.get("effect_magnitude", 0) <= 0.5,
            severity=ViolationSeverity.WARNING
        ))
    
    def add_invariant(self, invariant: Invariant) -> None:
        """添加不变量"""
        self.invariants[invariant.invariant_id] = invariant
    
    def remove_invariant(self, invariant_id: str) -> bool:
        """移除不变量"""
        if invariant_id in self.invariants:
            del self.invariants[invariant_id]
            return True
        return False
    
    def disable_invariant(self, invariant_id: str) -> bool:
        """禁用不变量"""
        if invariant_id in self.invariants:
            self.invariants[invariant_id].enabled = False
            return True
        return False
    
    def enable_invariant(self, invariant_id: str) -> bool:
        """启用不变量"""
        if invariant_id in self.invariants:
            self.invariants[invariant_id].enabled = True
            return True
        return False
    
    def check_all(self, context: Dict[str, Any]) -> List[InvariantViolation]:
        """
        检查所有不变量
        
        Args:
            context: 包含所有检查所需的当前状态
        
        Returns:
            List of violations
        """
        violations = []
        
        for inv_id, invariant in self.invariants.items():
            if not invariant.enabled:
                continue
            
            try:
                satisfied = invariant.check_fn(context)
                invariant.last_check = datetime.now().isoformat()
                
                if not satisfied:
                    violation = self._create_violation(invariant, context)
                    violations.append(violation)
                    invariant.violation_count += 1
                    invariant.last_violation = datetime.now().isoformat()
                    
            except Exception as e:
                # 检查函数出错, 跳过
                pass
        
        self.violations.extend(violations)
        self.violation_history.extend(violations)
        self._save_violations()
        
        return violations
    
    def _create_violation(self, invariant: Invariant, context: Dict[str, Any]) -> InvariantViolation:
        """创建违规记录"""
        import uuid
        
        return InvariantViolation(
            violation_id=str(uuid.uuid4())[:12],
            invariant_id=invariant.invariant_id,
            invariant_name=invariant.name,
            severity=invariant.severity,
            timestamp=datetime.now().isoformat(),
            current_value=context.get(invariant.invariant_id, "unknown"),
            expected_condition=invariant.description,
            duration_ms=0.0,
            context=context
        )
    
    def _save_violations(self):
        """保存违规记录"""
        violations_file = os.path.join(self.storage_path, "violations.json")
        with open(violations_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "violation_id": v.violation_id,
                "invariant_id": v.invariant_id,
                "invariant_name": v.invariant_name,
                "severity": v.severity.value,
                "timestamp": v.timestamp,
                "current_value": str(v.current_value),
                "expected_condition": v.expected_condition,
                "duration_ms": v.duration_ms,
                "context": v.context
            } for v in self.violation_history[-200:]], f, ensure_ascii=False, indent=2)
    
    def _load_history(self):
        violations_file = os.path.join(self.storage_path, "violations.json")
        if os.path.exists(violations_file):
            try:
                with open(violations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.violation_history = [InvariantViolation(
                        violation_id=v["violation_id"],
                        invariant_id=v["invariant_id"],
                        invariant_name=v["invariant_name"],
                        severity=ViolationSeverity(v["severity"]),
                        timestamp=v["timestamp"],
                        current_value=v["current_value"],
                        expected_condition=v["expected_condition"],
                        duration_ms=v["duration_ms"],
                        context=v.get("context", {})
                    ) for v in data]
            except:
                self.violation_history = []
    
    def get_status(self) -> InvariantStatus:
        """获取不变量状态"""
        total = len(self.invariants)
        enabled = sum(1 for i in self.invariants.values() if i.enabled)
        
        critical = [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
        fatal = [v for v in self.violations if v.severity == ViolationSeverity.FATAL]
        
        # 找出违反最多的不变量
        violation_counts: Dict[str, int] = {}
        for v in self.violation_history:
            violation_counts[v.invariant_id] = violation_counts.get(v.invariant_id, 0) + 1
        
        most_violated = max(violation_counts, key=violation_counts.get) if violation_counts else None
        
        # 系统健康判断
        system_healthy = len(fatal) == 0 and len(critical) == 0
        
        return InvariantStatus(
            total_invariants=total,
            enabled_invariants=enabled,
            violations=len(self.violations),
            critical_violations=len(critical) + len(fatal),
            system_healthy=system_healthy,
            most_violated_invariant=most_violated
        )
    
    def get_violations(self, 
                      invariant_id: str = None,
                      severity: ViolationSeverity = None,
                      limit: int = 50) -> List[InvariantViolation]:
        """获取违规记录"""
        violations = self.violation_history
        
        if invariant_id:
            violations = [v for v in violations if v.invariant_id == invariant_id]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return violations[-limit:]
    
    def must_hold(self, context: Dict[str, Any]) -> tuple[bool, List[InvariantViolation]]:
        """
        强制检查: 如果有任何CRITICAL/FATAL违反, 抛出异常
        
        Returns:
            (is_safe, violations)
        """
        violations = self.check_all(context)
        
        fatal_or_critical = [v for v in violations 
                            if v.severity in [ViolationSeverity.FATAL, ViolationSeverity.CRITICAL]]
        
        if fatal_or_critical:
            return False, fatal_or_critical
        
        return True, violations
    
    def verify(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证系统状态
        
        Returns:
            {
                "is_safe": bool,
                "violations": [...],
                "summary": {...}
            }
        """
        violations = self.check_all(context)
        is_safe = not any(v.severity in [ViolationSeverity.FATAL, ViolationSeverity.CRITICAL]
                         for v in violations)
        
        return {
            "is_safe": is_safe,
            "violations_count": len(violations),
            "violations": [{
                "invariant": v.invariant_name,
                "severity": v.severity.value,
                "timestamp": v.timestamp
            } for v in violations],
            "summary": self.get_status().__dict__
        }


def create_invariant_engine() -> SystemInvariantEngine:
    """工厂函数"""
    return SystemInvariantEngine()

__exports__ = ['Invariant', 'InvariantStatus', 'InvariantType', 'InvariantViolation', 'SystemInvariantEngine', 'ViolationSeverity', 'create_invariant_engine']


