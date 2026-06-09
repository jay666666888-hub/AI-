#!/usr/bin/env python3
"""
Long-Horizon Autonomy - 受控长期优化系统
P2-lite: Constrained Autonomous Optimizer

不是"完全自主 AI Agent"
而是"受控长期优化系统"

核心原则:
- Bounded goal generation (受限目标生成)
- Utility-filtered prioritization (效用过滤)
- Quota-based execution (配额执行)
- Autonomy Governor (自主性Governor)
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import time


class GoalStatus(Enum):
    PROPOSED = "proposed"
    PRIORITIZED = "prioritized"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GoalCategory(Enum):
    """目标类别 - 限定允许空间"""
    IMPROVE_SPEED = "improve_execution_speed"
    REDUCE_FAILURE = "reduce_failure_rate"
    CODE_QUALITY = "refactor_code_quality"
    COMPLETE_PENDING = "complete_pending_tasks"
    OPTIMIZE_LEARNING = "optimize_learning_policy"
    SYSTEM_MAINTENANCE = "system_maintenance"


class QuotaType(Enum):
    """配额类型"""
    GOALS_PER_HOUR = "goals_per_hour"
    GOALS_PER_DAY = "goals_per_day"
    EXECUTION_TIME_PER_GOAL = "execution_time_per_goal"
    SELF_TRIGGER_RATIO = "self_trigger_ratio"


@dataclass
class Goal:
    """目标"""
    goal_id: str
    category: GoalCategory
    description: str
    status: GoalStatus
    proposed_at: str
    proposed_by: str  # "system" | "user" | "self"
    expected_utility: float
    confidence: float
    system_value: float  # 对系统整体价值的评估
    priority_score: float  # 最终优先级分数
    planned_steps: int
    actual_steps: int
    time_budget_ms: int
    actual_time_ms: int
    context: Dict[str, Any]
    parent_goal_id: Optional[str] = None


@dataclass
class Quota:
    """配额"""
    quota_type: QuotaType
    limit: float
    used: float
    window_seconds: int
    last_reset: str


@dataclass
class AutonomyMetrics:
    """自主性指标"""
    total_goals_proposed: int
    system_proposed: int
    user_proposed: int
    self_proposed: int
    goals_completed: int
    goals_rejected: int
    avg_utility: float
    self_trigger_ratio: float
    quota_violations: int


class AutonomyGovernor:
    """
    Autonomy Governor - 自主性Governor
    
    限制:
    - goal生成频率
    - goal复杂度
    - self-trigger比例
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/autonomy"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 配额配置
        self.quotas: Dict[QuotaType, Quota] = {
            QuotaType.GOALS_PER_HOUR: Quota(
                quota_type=QuotaType.GOALS_PER_HOUR,
                limit=10.0,
                used=0.0,
                window_seconds=3600,
                last_reset=datetime.now().isoformat()
            ),
            QuotaType.GOALS_PER_DAY: Quota(
                quota_type=QuotaType.GOALS_PER_DAY,
                limit=50.0,
                used=0.0,
                window_seconds=86400,
                last_reset=datetime.now().isoformat()
            ),
            QuotaType.EXECUTION_TIME_PER_GOAL: Quota(
                quota_type=QuotaType.EXECUTION_TIME_PER_GOAL,
                limit=300000.0,  # 5分钟
                used=0.0,
                window_seconds=1,
                last_reset=datetime.now().isoformat()
            ),
            QuotaType.SELF_TRIGGER_RATIO: Quota(
                quota_type=QuotaType.SELF_TRIGGER_RATIO,
                limit=0.2,  # 20% 最高自触发比例
                used=0.0,
                window_seconds=3600,
                last_reset=datetime.now().isoformat()
            ),
        }
        
        # 复杂度限制
        self.max_goal_complexity = 5  # 最多5个步骤
        self.max_planning_horizon = 3  # 最多3步预瞄
        
        # 允许的目标空间
        self.allowed_goal_space = [
            GoalCategory.IMPROVE_SPEED,
            GoalCategory.REDUCE_FAILURE,
            GoalCategory.CODE_QUALITY,
            GoalCategory.COMPLETE_PENDING,
            GoalCategory.OPTIMIZE_LEARNING,
            GoalCategory.SYSTEM_MAINTENANCE,
        ]
        
        self._load_quotas()
    
    def _load_quotas(self):
        quotas_file = os.path.join(self.storage_path, "quotas.json")
        if os.path.exists(quotas_file):
            try:
                with open(quotas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for qt_str, q_data in data.items():
                        qt = QuotaType(qt_str)
                        self.quotas[qt].used = q_data.get("used", 0.0)
                        self.quotas[qt].last_reset = q_data.get("last_reset", datetime.now().isoformat())
            except:
                pass
    
    def _save_quotas(self):
        quotas_file = os.path.join(self.storage_path, "quotas.json")
        data = {qt.value: {"used": q.used, "last_reset": q.last_reset} 
                for qt, q in self.quotas.items()}
        with open(quotas_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _reset_if_needed(self, quota: Quota):
        """检查是否需要重置配额"""
        last_reset = datetime.fromisoformat(quota.last_reset)
        now = datetime.now()
        
        if (now - last_reset).total_seconds() >= quota.window_seconds:
            quota.used = 0.0
            quota.last_reset = now.isoformat()
    
    def can_propose_goal(self, proposed_by: str = "system") -> tuple[bool, str]:
        """
        检查是否可以提议新目标
        
        Returns:
            (can_propose, reason)
        """
        # 检查 GOALS_PER_HOUR
        hourly = self.quotas[QuotaType.GOALS_PER_HOUR]
        self._reset_if_needed(hourly)
        
        if hourly.used >= hourly.limit:
            return False, f"小时配额已满: {hourly.used}/{hourly.limit}"
        
        # 检查 GOALS_PER_DAY
        daily = self.quotas[QuotaType.GOALS_PER_DAY]
        self._reset_if_needed(daily)
        
        if daily.used >= daily.limit:
            return False, f"日配额已满: {daily.used}/{daily.limit}"
        
        # 检查 SELF_TRIGGER_RATIO
        if proposed_by == "self":
            ratio_quota = self.quotas[QuotaType.SELF_TRIGGER_RATIO]
            self._reset_if_needed(ratio_quota)
            
            # 计算当前自触发比例
            total_proposed = hourly.used + 1  # +1 for this proposal
            self_ratio = ratio_quota.used + 1 if proposed_by == "self" else ratio_quota.used
            current_ratio = self_ratio / total_proposed if total_proposed > 0 else 0
            
            if current_ratio > ratio_quota.limit:
                return False, f"自触发比例超限: {current_ratio:.2%} > {ratio_quota.limit:.2%}"
        
        return True, "允许提议"
    
    def can_execute_goal(self, estimated_time_ms: int) -> tuple[bool, str]:
        """检查是否可以执行目标"""
        time_quota = self.quotas[QuotaType.EXECUTION_TIME_PER_GOAL]
        self._reset_if_needed(time_quota)
        
        if time_quota.used + estimated_time_ms > time_quota.limit:
            return False, f"时间配额不足: 已用 {time_quota.used}ms, 限制 {time_quota.limit}ms"
        
        return True, "允许执行"
    
    def record_goal_proposed(self, proposed_by: str):
        """记录目标提议"""
        hourly = self.quotas[QuotaType.GOALS_PER_HOUR]
        daily = self.quotas[QuotaType.GOALS_PER_DAY]
        
        self._reset_if_needed(hourly)
        self._reset_if_needed(daily)
        
        hourly.used += 1
        daily.used += 1
        
        if proposed_by == "self":
            ratio_quota = self.quotas[QuotaType.SELF_TRIGGER_RATIO]
            self._reset_if_needed(ratio_quota)
            ratio_quota.used += 1
        
        self._save_quotas()
    
    def record_goal_completed(self, actual_time_ms: int, utility: float):
        """记录目标完成"""
        time_quota = self.quotas[QuotaType.EXECUTION_TIME_PER_GOAL]
        self._reset_if_needed(time_quota)
        time_quota.used += actual_time_ms
        self._save_quotas()
    
    def is_category_allowed(self, category: GoalCategory) -> bool:
        """检查目标类别是否在允许空间"""
        return category in self.allowed_goal_space
    
    def is_complexity_allowed(self, steps: int) -> bool:
        """检查复杂度是否允许"""
        return steps <= self.max_goal_complexity
    
    def get_metrics(self) -> AutonomyMetrics:
        """获取自主性指标"""
        hourly = self.quotas[QuotaType.GOALS_PER_HOUR]
        self._reset_if_needed(hourly)
        
        metrics_file = os.path.join(self.storage_path, "metrics.json")
        metrics = AutonomyMetrics(
            total_goals_proposed=int(hourly.used),
            system_proposed=0,
            user_proposed=0,
            self_proposed=int(self.quotas[QuotaType.SELF_TRIGGER_RATIO].used),
            goals_completed=0,
            goals_rejected=0,
            avg_utility=0.0,
            self_trigger_ratio=self.quotas[QuotaType.SELF_TRIGGER_RATIO].used / max(1, hourly.used),
            quota_violations=0
        )
        
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metrics.total_goals_proposed = data.get("total_proposed", int(hourly.used))
                    metrics.goals_completed = data.get("completed", 0)
                    metrics.goals_rejected = data.get("rejected", 0)
                    metrics.avg_utility = data.get("avg_utility", 0.0)
            except:
                pass
        
        return metrics


class GoalGenerator:
    """
    Goal Generator - 受限目标生成器
    
    不是自由生成目标
    allowed_goal_space = [
        "improve_execution_speed",
        "reduce_failure_rate", 
        "refactor_code_quality",
        "complete_pending_tasks"
    ]
    """
    
    def __init__(self, autonomy_governor: AutonomyGovernor):
        self.governor = autonomy_governor
        
        # 目标模板
        self.goal_templates: Dict[GoalCategory, Callable] = {
            GoalCategory.IMPROVE_SPEED: self._generate_speed_goal,
            GoalCategory.REDUCE_FAILURE: self._generate_failure_goal,
            GoalCategory.CODE_QUALITY: self._generate_quality_goal,
            GoalCategory.COMPLETE_PENDING: self._generate_pending_goal,
            GoalCategory.OPTIMIZE_LEARNING: self._generate_learning_goal,
            GoalCategory.SYSTEM_MAINTENANCE: self._generate_maintenance_goal,
        }
    
    def generate_goals(self,
                       system_state: Dict[str, Any],
                       context: Dict[str, Any],
                       max_goals: int = 3) -> List[Goal]:
        """
        生成目标列表
        
        受限生成:
        1. 只能在 allowed_goal_space
        2. 必须通过 autonomy_governor 审查
        3. 复杂度受限
        """
        generated = []
        
        for category, generator_fn in self.goal_templates.items():
            if not self.governor.is_category_allowed(category):
                continue
            
            # 检查配额
            can_propose, reason = self.governor.can_propose_goal("system")
            if not can_propose:
                continue
            
            # 生成目标
            goal = generator_fn(system_state, context)
            if goal:
                # 复杂度检查
                if not self.governor.is_complexity_allowed(goal.planned_steps):
                    goal.planned_steps = self.governor.max_goal_complexity
                
                generated.append(goal)
                
                if len(generated) >= max_goals:
                    break
        
        return generated
    
    def generate_self_goal(self,
                          system_state: Dict[str, Any],
                          context: Dict[str, Any]) -> Optional[Goal]:
        """
        系统自生成目标 (更严格限制)
        """
        # 先检查自触发配额
        can_propose, reason = self.governor.can_propose_goal("self")
        if not can_propose:
            return None
        
        # 基于系统状态选择类别
        category = self._select_based_on_state(system_state)
        
        if not category or not self.governor.is_category_allowed(category):
            return None
        
        generator_fn = self.goal_templates.get(category)
        if not generator_fn:
            return None
        
        goal = generator_fn(system_state, context)
        if goal:
            goal.proposed_by = "self"
            return goal
        
        return None
    
    def _select_based_on_state(self, state: Dict[str, Any]) -> Optional[GoalCategory]:
        """基于系统状态选择目标类别"""
        # 分析系统状态, 选择最需要的目标类别
        if state.get("failure_rate", 0) > 0.2:
            return GoalCategory.REDUCE_FAILURE
        elif state.get("avg_execution_time", 0) > state.get("target_time", float('inf')):
            return GoalCategory.IMPROVE_SPEED
        elif state.get("pending_tasks", 0) > 5:
            return GoalCategory.COMPLETE_PENDING
        elif state.get("code_quality_score", 1.0) < 0.7:
            return GoalCategory.CODE_QUALITY
        elif state.get("learning_stagnant", False):
            return GoalCategory.OPTIMIZE_LEARNING
        
        return GoalCategory.SYSTEM_MAINTENANCE
    
    def _generate_speed_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.IMPROVE_SPEED,
            description="Improve execution speed",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.7,
            confidence=0.6,
            system_value=0.8,
            priority_score=0.0,
            planned_steps=min(3, self.governor.max_planning_horizon),
            actual_steps=0,
            time_budget_ms=60000,
            actual_time_ms=0,
            context=context
        )
    
    def _generate_failure_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.REDUCE_FAILURE,
            description="Reduce system failure rate",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.8,
            confidence=0.7,
            system_value=0.9,
            priority_score=0.0,
            planned_steps=min(4, self.governor.max_planning_horizon),
            actual_steps=0,
            time_budget_ms=120000,
            actual_time_ms=0,
            context=context
        )
    
    def _generate_quality_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.CODE_QUALITY,
            description="Refactor and improve code quality",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.6,
            confidence=0.5,
            system_value=0.7,
            priority_score=0.0,
            planned_steps=min(5, self.governor.max_planning_horizon),
            actual_steps=0,
            time_budget_ms=180000,
            actual_time_ms=0,
            context=context
        )
    
    def _generate_pending_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        pending = state.get("pending_tasks", 0)
        if pending == 0:
            return None
        
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.COMPLETE_PENDING,
            description=f"Complete {min(pending, 5)} pending tasks",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.9,
            confidence=0.9,
            system_value=0.8,
            priority_score=0.0,
            planned_steps=min(pending, 3),
            actual_steps=0,
            time_budget_ms=pending * 30000,
            actual_time_ms=0,
            context=context
        )
    
    def _generate_learning_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.OPTIMIZE_LEARNING,
            description="Optimize learning policy based on recent experiences",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.7,
            confidence=0.5,
            system_value=0.6,
            priority_score=0.0,
            planned_steps=2,
            actual_steps=0,
            time_budget_ms=30000,
            actual_time_ms=0,
            context=context
        )
    
    def _generate_maintenance_goal(self, state: Dict, context: Dict) -> Optional[Goal]:
        return Goal(
            goal_id=str(uuid.uuid4())[:12],
            category=GoalCategory.SYSTEM_MAINTENANCE,
            description="System maintenance and cleanup",
            status=GoalStatus.PROPOSED,
            proposed_at=datetime.now().isoformat(),
            proposed_by="system",
            expected_utility=0.5,
            confidence=0.8,
            system_value=0.5,
            priority_score=0.0,
            planned_steps=2,
            actual_steps=0,
            time_budget_ms=60000,
            actual_time_ms=0,
            context=context
        )


class GoalPrioritizer:
    """
    Goal Prioritizer - 基于utility的优先级计算
    
    goal_score = expected_utility × confidence × system_value
    """
    
    def __init__(self):
        self.urgency_weights = {
            GoalCategory.IMPROVE_SPEED: 1.2,
            GoalCategory.REDUCE_FAILURE: 1.5,  # 失败问题优先级更高
            GoalCategory.CODE_QUALITY: 0.8,
            GoalCategory.COMPLETE_PENDING: 1.0,
            GoalCategory.OPTIMIZE_LEARNING: 0.7,
            GoalCategory.SYSTEM_MAINTENANCE: 0.6,
        }
    
    def calculate_priority(self, goal: Goal) -> float:
        """
        计算优先级分数
        
        goal_score = expected_utility × confidence × system_value × urgency_weight
        """
        base_score = goal.expected_utility * goal.confidence * goal.system_value
        
        urgency = self.urgency_weights.get(goal.category, 1.0)
        
        # 时间衰减 (如果目标过期,降低优先级)
        age_hours = (datetime.now() - datetime.fromisoformat(goal.proposed_at)).total_seconds() / 3600
        time_decay = max(0.5, 1.0 - age_hours * 0.1)
        
        priority = base_score * urgency * time_decay
        
        return max(0.0, min(1.0, priority))
    
    def prioritize(self, goals: List[Goal]) -> List[Goal]:
        """对目标列表进行优先级排序"""
        for goal in goals:
            goal.priority_score = self.calculate_priority(goal)
        
        return sorted(goals, key=lambda g: g.priority_score, reverse=True)


class Scheduler:
    """
    Scheduler - 受限调度器
    
    关键限制:
    - time-boxed execution (时间盒执行)
    - quota-based execution (配额执行)
    - bounded planning horizon (受限规划视野, 3-5步)
    """
    
    def __init__(self, autonomy_governor: AutonomyGovernor):
        self.governor = autonomy_governor
        self.max_execution_time_ms = 300000  # 5分钟
        self.max_steps_per_goal = 5
    
    def can_schedule(self, goal: Goal) -> tuple[bool, str]:
        """检查是否可以调度"""
        # 时间配额检查
        can_exec, reason = self.governor.can_execute_goal(goal.time_budget_ms)
        if not can_exec:
            return False, reason
        
        # 复杂度检查
        if goal.planned_steps > self.max_steps_per_goal:
            return False, f"目标复杂度超限: {goal.planned_steps} > {self.max_steps_per_goal}"
        
        return True, "可以调度"
    
    def schedule(self, goals: List[Goal]) -> List[Goal]:
        """
        调度目标
        
        只调度可以通过检查的目标
        """
        scheduled = []
        
        for goal in goals:
            can_sched, reason = self.can_schedule(goal)
            
            if can_sched:
                goal.status = GoalStatus.SCHEDULED
                scheduled.append(goal)
            else:
                goal.status = GoalStatus.REJECTED
                goal.context["rejection_reason"] = reason
        
        return scheduled
    
    def time_box_execution(self, goal: Goal, execution_fn: Callable) -> Any:
        """
        时间盒执行
        
        在指定时间盒内执行,超时则停止
        """
        start_time = time.time()
        remaining_time = goal.time_budget_ms / 1000
        
        try:
            result = execution_fn(time_budget=remaining_time)
            
            actual_time = (time.time() - start_time) * 1000
            goal.actual_time_ms = int(actual_time)
            
            return result
        
        except TimeoutError:
            goal.actual_time_ms = goal.time_budget_ms
            goal.status = GoalStatus.EXPIRED
            return {"status": "timeout", "goal_id": goal.goal_id}


class LongHorizonAutonomy:
    """
    Long-Horizon Autonomy - 主入口
    
    受控长期优化系统
    
    数据流:
        GoalGenerator
          → GoalPrioritizer (utility-filtered)
            → Scheduler (quota-bounded)
              → AutonomyGovernor (safety checks)
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/autonomy"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.governor = AutonomyGovernor(storage_path)
        self.generator = GoalGenerator(self.governor)
        self.prioritizer = GoalPrioritizer()
        self.scheduler = Scheduler(self.governor)
        
        self.goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        
        self._load_goals()
    
    def _load_goals(self):
        goals_file = os.path.join(self.storage_path, "goals.json")
        if os.path.exists(goals_file):
            try:
                with open(goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.goals = [Goal(**g) for g in data.get("active", [])]
                    self.completed_goals = [Goal(**g) for g in data.get("completed", [])]
            except:
                self.goals = []
                self.completed_goals = []
    
    def _save_goals(self):
        goals_file = os.path.join(self.storage_path, "goals.json")
        with open(goals_file, 'w', encoding='utf-8') as f:
            json.dump({
                "active": [{
                    "goal_id": g.goal_id,
                    "category": g.category.value,
                    "description": g.description,
                    "status": g.status.value,
                    "proposed_at": g.proposed_at,
                    "proposed_by": g.proposed_by,
                    "expected_utility": g.expected_utility,
                    "confidence": g.confidence,
                    "system_value": g.system_value,
                    "priority_score": g.priority_score,
                    "planned_steps": g.planned_steps,
                    "actual_steps": g.actual_steps,
                    "time_budget_ms": g.time_budget_ms,
                    "actual_time_ms": g.actual_time_ms,
                    "context": g.context,
                    "parent_goal_id": g.parent_goal_id
                } for g in self.goals],
                "completed": [{
                    "goal_id": g.goal_id,
                    "category": g.category.value,
                    "description": g.description,
                    "status": g.status.value,
                    "proposed_at": g.proposed_at,
                    "proposed_by": g.proposed_by,
                    "expected_utility": g.expected_utility,
                    "actual_time_ms": g.actual_time_ms,
                    "context": g.context
                } for g in self.completed_goals[-50:]]
            }, f, ensure_ascii=False, indent=2)
    
    def propose_goals(self,
                     system_state: Dict[str, Any],
                     context: Dict[str, Any],
                     max_goals: int = 3) -> List[Goal]:
        """
        提议新目标
        
        入口: 生成 → 优先级 → 调度
        """
        # 1. 生成
        new_goals = self.generator.generate_goals(system_state, context, max_goals)
        
        # 2. 优先级计算
        prioritized = self.prioritizer.prioritize(new_goals)
        
        # 3. 调度
        scheduled = self.scheduler.schedule(prioritized)
        
        # 4. 记录
        for goal in scheduled:
            self.governor.record_goal_proposed(goal.proposed_by)
        
        self.goals.extend(scheduled)
        self._save_goals()
        
        return scheduled
    
    def execute_next_goal(self, execution_fn: Callable) -> Optional[Dict[str, Any]]:
        """
        执行下一个最高优先级目标
        
        Args:
            execution_fn: 执行函数, 接收 goal 和 time_budget
            
        Returns:
            执行结果
        """
        if not self.goals:
            return None
        
        # 获取最高优先级目标
        self.goals = self.prioritizer.prioritize(self.goals)
        
        goal = self.goals[0]
        goal.status = GoalStatus.IN_PROGRESS
        
        # 时间盒执行
        start = time.time()
        
        try:
            result = self.scheduler.time_box_execution(goal, execution_fn)
            
            actual_time = (time.time() - start) * 1000
            goal.actual_time_ms = int(actual_time)
            goal.actual_steps = goal.planned_steps
            
            if goal.status != GoalStatus.EXPIRED:
                goal.status = GoalStatus.COMPLETED
                self.completed_goals.append(goal)
                self.goals.remove(goal)
            
            self.governor.record_goal_completed(goal.actual_time_ms, goal.expected_utility)
            
            return {
                "status": "completed",
                "goal_id": goal.goal_id,
                "actual_time_ms": goal.actual_time_ms,
                "result": result
            }
        
        except Exception as e:
            goal.status = GoalStatus.REJECTED
            goal.context["error"] = str(e)
            
            return {
                "status": "failed",
                "goal_id": goal.goal_id,
                "error": str(e)
            }
        
        finally:
            self._save_goals()
    
    def get_next_goal(self) -> Optional[Goal]:
        """获取下一个待执行目标"""
        if not self.goals:
            return None
        
        prioritized = self.prioritizer.prioritize(self.goals)
        return prioritized[0]
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return self.goals
    
    def get_completed_goals(self, limit: int = 10) -> List[Goal]:
        """获取已完成目标"""
        return self.completed_goals[-limit:]
    
    def cancel_goal(self, goal_id: str) -> bool:
        """取消目标"""
        goal = next((g for g in self.goals if g.goal_id == goal_id), None)
        if not goal:
            return False
        
        goal.status = GoalStatus.CANCELLED
        self.goals.remove(goal)
        self._save_goals()
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "active_goals": len(self.goals),
            "completed_goals": len(self.completed_goals),
            "governor_metrics": {
                "self_trigger_ratio": self.governor.get_metrics().self_trigger_ratio,
                "goals_per_hour_used": self.governor.quotas[QuotaType.GOALS_PER_HOUR].used,
                "goals_per_hour_limit": self.governor.quotas[QuotaType.GOALS_PER_HOUR].limit,
            },
            "next_goal": self.get_next_goal().goal_id if self.get_next_goal() else None
        }


def create_long_horizon_autonomy() -> LongHorizonAutonomy:
    """工厂函数"""
    return LongHorizonAutonomy()

__exports__ = ['AutonomyGovernor', 'AutonomyMetrics', 'Goal', 'GoalCategory', 'GoalGenerator', 'GoalPrioritizer', 'GoalStatus', 'LongHorizonAutonomy', 'Quota', 'QuotaType', 'Scheduler', 'create_long_horizon_autonomy']


