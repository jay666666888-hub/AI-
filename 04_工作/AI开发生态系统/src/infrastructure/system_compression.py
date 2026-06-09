#!/usr/bin/env python3
"""
System Compression - 系统压缩
Step 1: 减少系统"自由度"

目标:
- 合并三大核心流 (Execution, Decision, Learning) → Runtime Core Loop
- Policy mutation surface 收缩
- Decision graph 简化 (linear + bounded branching)
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class PathType(Enum):
    """路径类型枚举"""
    EXECUTION = "execution"
    DECISION = "decision"
    LEARNING = "learning"
    REFLECTION = "reflection"


@dataclass
class UnifiedPath:
    """统一路径"""
    path_id: str
    path_type: PathType
    stages: List[str]  # 阶段列表
    entry_point: str
    exit_point: str
    allowed_mutations: Set[str]  # 允许的变更类型
    forbidden_mutations: Set[str]  # 禁止的变更类型


@dataclass
class MutationPermission:
    """变更权限"""
    mutation_type: str
    allowed: bool
    scope: str  # "global", "local", "none"
    reason: str


@dataclass
class CoreLoopConfig:
    """核心循环配置"""
    execution_stage: str = "execute"
    decision_stage: str = "decide"
    learning_stage: str = "learn"
    reflection_stage: str = "reflect"
    
    # 边界限制
    max_branching: int = 3
    max_depth: int = 5
    max_concurrent_paths: int = 5
    
    # 允许的变更范围
    allowed_weights: List[str] = None  # ["utility_weight", "skill_rank"]
    forbidden_changes: List[str] = None  # ["agent_structure", "pipeline"]
    
    def __post_init__(self):
        if self.allowed_weights is None:
            self.allowed_weights = ["utility_weight", "skill_rank", "selection_probability"]
        if self.forbidden_changes is None:
            self.forbidden_changes = ["agent_structure", "pipeline_structure", "skill_order"]


class PathMerger:
    """
    Path Merger - 路径合并器
    
    将 Execution Flow, Decision Flow, Learning Flow 合并为 Runtime Core Loop
    """
    
    def __init__(self):
        self.unified_paths: Dict[str, UnifiedPath] = {}
        self.core_loop_stages = [
            "plan",      # 规划阶段
            "decide",    # 决策阶段
            "execute",   # 执行阶段
            "learn",     # 学习阶段
            "reflect",   # 反思阶段
        ]
    
    def create_unified_path(self,
                           path_id: str,
                           path_type: PathType,
                           stages: List[str]) -> UnifiedPath:
        """创建统一路径"""
        # 验证 stages 是否符合核心循环
        valid_stages = set(self.core_loop_stages)
        for stage in stages:
            if stage not in valid_stages:
                raise ValueError(f"Invalid stage: {stage}. Must be one of {valid_stages}")
        
        # 限制分支数量
        if len(stages) > 5:
            stages = stages[:5]
        
        path = UnifiedPath(
            path_id=path_id,
            path_type=path_type,
            stages=stages,
            entry_point=stages[0],
            exit_point=stages[-1],
            allowed_mutations=set(),
            forbidden_mutations=set()
        )
        
        self.unified_paths[path_id] = path
        return path
    
    def define_mutation_scope(self, path_id: str) -> MutationPermission:
        """定义路径的变更权限"""
        path = self.unified_paths.get(path_id)
        if not path:
            return MutationPermission("", False, "none", "path not found")
        
        # Execution Path: 只允许权重调整
        if path.path_type == PathType.EXECUTION:
            return MutationPermission(
                mutation_type="weight_adjustment",
                allowed=True,
                scope="local",
                reason="Execution path only allows parameter changes"
            )
        
        # Decision Path: 只允许评分调整
        if path.path_type == PathType.DECISION:
            return MutationPermission(
                mutation_type="scoring_adjustment",
                allowed=True,
                scope="local",
                reason="Decision path only allows score changes"
            )
        
        # Learning Path: 只允许策略参数更新
        if path.path_type == PathType.LEARNING:
            return MutationPermission(
                mutation_type="policy_parameter_update",
                allowed=True,
                scope="local",
                reason="Learning path only allows parameter evolution"
            )
        
        return MutationPermission(
            mutation_type="none",
            allowed=False,
            scope="none",
            reason="Path type not allowed for mutation"
        )
    
    def get_core_loop(self) -> List[str]:
        """获取核心循环阶段"""
        return self.core_loop_stages.copy()
    
    def validate_path_linearity(self, path: UnifiedPath) -> bool:
        """验证路径是否线性（无环）"""
        # 检查是否有重复阶段（可能表示循环）
        return len(path.stages) == len(set(path.stages))
    
    def merge_execution_decision_learning(self) -> UnifiedPath:
        """合并三大核心流"""
        # 验证所有路径是否可以合并
        merged_stages = ["plan", "decide", "execute", "learn", "reflect"]
        
        return UnifiedPath(
            path_id="runtime_core_loop",
            path_type=PathType.EXECUTION,
            stages=merged_stages,
            entry_point="plan",
            exit_point="reflect",
            allowed_mutations={"utility_weight", "skill_rank", "selection_probability"},
            forbidden_mutations={"agent_structure", "pipeline", "skill_order"}
        )


class PolicyMutationSurface:
    """
    Policy Mutation Surface - 策略变更范围收缩
    
    只允许:
    - utility weight adjustment
    - skill ranking adjustment
    
    禁止:
    - agent结构变化
    - pipeline动态重写
    """
    
    def __init__(self, config: CoreLoopConfig = None):
        self.config = config or CoreLoopConfig()
        
        # 允许的变更类型
        self.allowed_mutations = {
            "utility_weight": self._validate_utility_weight,
            "skill_rank": self._validate_skill_rank,
            "selection_probability": self._validate_selection_prob,
            "learning_rate": self._validate_learning_rate,
            "threshold_adjustment": self._validate_threshold,
        }
        
        # 禁止的变更类型
        self.forbidden_mutations = {
            "agent_structure": self._block_agent_structure,
            "pipeline_structure": self._block_pipeline,
            "skill_order": self._block_skill_order,
            "agent_count": self._block_agent_count,
            "layer_architecture": self._block_layer_architecture,
        }
    
    def can_mutate(self, mutation_type: str, value: Any) -> tuple[bool, str]:
        """
        检查是否可以变更
        
        Returns:
            (can_mutate, reason)
        """
        # 检查是否在禁止列表
        if mutation_type in self.forbidden_mutations:
            validator = self.forbidden_mutations[mutation_type]
            return False, validator(value)
        
        # 检查是否在允许列表
        if mutation_type in self.allowed_mutations:
            validator = self.allowed_mutations[mutation_type]
            is_valid, reason = validator(value)
            return is_valid, reason
        
        # 不在任何列表中，默认禁止
        return False, f"Unknown mutation type: {mutation_type}"
    
    def _validate_utility_weight(self, value: Any) -> tuple[bool, str]:
        """验证 utility weight 变更"""
        if not isinstance(value, (int, float)):
            return False, "utility_weight must be numeric"
        if not 0.0 <= value <= 1.0:
            return False, "utility_weight must be in [0, 1]"
        return True, "allowed"
    
    def _validate_skill_rank(self, value: Any) -> tuple[bool, str]:
        """验证 skill rank 变更"""
        if isinstance(value, dict):
            # 验证 rank 值
            for k, v in value.items():
                if not isinstance(v, (int, float)):
                    return False, f"skill_rank value for {k} must be numeric"
        return True, "allowed"
    
    def _validate_selection_prob(self, value: Any) -> tuple[bool, str]:
        """验证选择概率变更"""
        if isinstance(value, (int, float)):
            if not 0.0 <= value <= 1.0:
                return False, "selection_probability must be in [0, 1]"
        elif isinstance(value, dict):
            total = sum(v for v in value.values() if isinstance(v, (int, float)))
            # 允许概率和不为1（归一化后即可）
        return True, "allowed"
    
    def _validate_learning_rate(self, value: Any) -> tuple[bool, str]:
        """验证学习率变更"""
        if not isinstance(value, (int, float)):
            return False, "learning_rate must be numeric"
        if value <= 0 or value > 1.0:
            return False, "learning_rate must be in (0, 1]"
        return True, "allowed"
    
    def _validate_threshold(self, value: Any) -> tuple[bool, str]:
        """验证阈值调整"""
        if not isinstance(value, (int, float)):
            return False, "threshold must be numeric"
        return True, "allowed"
    
    def _block_agent_structure(self, value: Any) -> str:
        return "BLOCKED: agent_structure mutation not allowed"
    
    def _block_pipeline(self, value: Any) -> str:
        return "BLOCKED: pipeline_structure mutation not allowed"
    
    def _block_skill_order(self, value: Any) -> str:
        return "BLOCKED: skill_order mutation not allowed"
    
    def _block_agent_count(self, value: Any) -> str:
        return "BLOCKED: agent_count mutation not allowed"
    
    def _block_layer_architecture(self, value: Any) -> str:
        return "BLOCKED: layer_architecture mutation not allowed"
    
    def get_mutation_surface(self) -> Dict[str, bool]:
        """获取变更面摘要"""
        return {
            "allowed": list(self.allowed_mutations.keys()),
            "forbidden": list(self.forbidden_mutations.keys())
        }


class DecisionGraphSimplifier:
    """
    Decision Graph Simplifier - 决策图简化
    
    从 DAG/multi-agent graph → linear + bounded branching
    """
    
    def __init__(self, max_branching: int = 3, max_depth: int = 5):
        self.max_branching = max_branching
        self.max_depth = max_depth
    
    def simplify_to_linear(self, 
                          nodes: List[str],
                          edges: List[tuple[str, str]]) -> Dict[str, Any]:
        """
        简化为线性 + bounded branching 结构
        
        Args:
            nodes: 节点列表
            edges: 边列表 [(source, target), ...]
        
        Returns:
            simplified graph structure
        """
        if not nodes:
            return {"nodes": [], "edges": [], "is_linear": True}
        
        # 检查是否已经是线性的
        is_linear = self._check_linearity(nodes, edges)
        
        if is_linear:
            return {
                "nodes": nodes,
                "edges": edges,
                "is_linear": True,
                "branching_count": 1
            }
        
        # 需要简化
        # 1. 找到汇聚点
        # 2. 合并分支
        # 3. 限制深度
        
        simplified_nodes = self._limit_depth(nodes)
        simplified_edges = self._limit_branching(edges)
        
        return {
            "nodes": simplified_nodes,
            "edges": simplified_edges,
            "is_linear": len(simplified_edges) <= len(simplified_nodes),
            "branching_count": self._count_branching(edges),
            "original_nodes": len(nodes),
            "simplified_nodes": len(simplified_nodes)
        }
    
    def _check_linearity(self, nodes: List[str], edges: List[tuple[str, str]]) -> bool:
        """检查是否线性"""
        if len(edges) > len(nodes) - 1:
            return False  # 有环
        
        # 检查每个节点的入度和出度
        in_degree = {n: 0 for n in nodes}
        out_degree = {n: 0 for n in nodes}
        
        for src, tgt in edges:
            if src in in_degree and tgt in out_degree:
                in_degree[tgt] += 1
                out_degree[src] += 1
        
        # 线性图: 最多一个节点入度为0（起点），最多一个节点出度为0（终点）
        start_nodes = [n for n in nodes if in_degree[n] == 0]
        end_nodes = [n for n in nodes if out_degree[n] == 0]
        
        return len(start_nodes) <= 1 and len(end_nodes) <= 1
    
    def _limit_depth(self, nodes: List[str]) -> List[str]:
        """限制深度"""
        if len(nodes) <= self.max_depth:
            return nodes
        
        # 保留首尾，压缩中间
        kept = [nodes[0]]
        
        step = (len(nodes) - 2) / (self.max_depth - 1)
        for i in range(1, self.max_depth - 1):
            idx = int(i * step)
            kept.append(nodes[idx + 1])  # +1 to skip first
        
        kept.append(nodes[-1])
        
        return kept
    
    def _limit_branching(self, edges: List[tuple[str, str]]) -> List[tuple[str, str]]:
        """限制分支数"""
        if len(edges) <= self.max_branching:
            return edges
        
        # 保留主路径，裁剪分支
        # 简化策略: 按入度排序，保留主分支
        in_degree = {}
        for src, tgt in edges:
            if tgt not in in_degree:
                in_degree[tgt] = 0
            in_degree[tgt] += 1
        
        # 保留入度最高的边
        sorted_edges = sorted(edges, key=lambda e: in_degree.get(e[1], 0), reverse=True)
        return sorted_edges[:self.max_branching]
    
    def _count_branching(self, edges: List[tuple[str, str]]) -> int:
        """计算分支数"""
        targets = [e[1] for e in edges]
        unique_targets = set(targets)
        
        # 每个唯一目标算一个分支
        return len(unique_targets)


class SystemCompressor:
    """
    System Compressor - 系统压缩主引擎
    
    Step 1: 减少系统复杂度
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/compression"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.path_merger = PathMerger()
        self.policy_surface = PolicyMutationSurface()
        self.graph_simplifier = DecisionGraphSimplifier()
        
        self.compression_history: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self):
        history_file = os.path.join(self.storage_path, "compression_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.compression_history = json.load(f)
            except:
                self.compression_history = []
    
    def _save(self):
        history_file = os.path.join(self.storage_path, "compression_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.compression_history[-50:], f, ensure_ascii=False, indent=2)
    
    def compress_execution_flow(self) -> Dict[str, Any]:
        """压缩执行流"""
        # 创建统一的 Runtime Core Loop
        core_loop = self.path_merger.merge_execution_decision_learning()
        
        # 定义阶段
        stages = ["plan", "decide", "execute", "learn", "reflect"]
        
        self.compression_history.append({
            "action": "compress_execution_flow",
            "timestamp": datetime.now().isoformat(),
            "result": {
                "core_loop_stages": stages,
                "path_id": core_loop.path_id,
                "is_linear": True,
                "branching_count": 1
            }
        })
        
        self._save()
        
        return {
            "core_loop_stages": stages,
            "path_id": core_loop.path_id,
            "max_branching": 1,
            "max_depth": len(stages)
        }
    
    def compress_decision_paths(self,
                               nodes: List[str],
                               edges: List[tuple[str, str]]) -> Dict[str, Any]:
        """压缩决策路径"""
        simplified = self.graph_simplifier.simplify_to_linear(nodes, edges)
        
        self.compression_history.append({
            "action": "compress_decision_paths",
            "timestamp": datetime.now().isoformat(),
            "result": simplified
        })
        
        self._save()
        
        return simplified
    
    def validate_mutation(self, mutation_type: str, value: Any) -> Dict[str, Any]:
        """验证变更是否允许"""
        can_mutate, reason = self.policy_surface.can_mutate(mutation_type, value)
        
        return {
            "mutation_type": mutation_type,
            "allowed": can_mutate,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def lock_system_structure(self) -> Dict[str, Any]:
        """
        锁定系统结构
        
        生成不可变配置快照
        """
        lock_config = {
            "locked_at": datetime.now().isoformat(),
            "allowed_mutations": list(self.policy_surface.allowed_mutations.keys()),
            "forbidden_mutations": list(self.policy_surface.forbidden_mutations.keys()),
            "core_loop_stages": self.path_merger.get_core_loop(),
            "max_branching": self.graph_simplifier.max_branching,
            "max_depth": self.graph_simplifier.max_depth
        }
        
        lock_file = os.path.join(self.storage_path, "structure_lock.json")
        with open(lock_file, 'w', encoding='utf-8') as f:
            json.dump(lock_config, f, ensure_ascii=False, indent=2)
        
        self.compression_history.append({
            "action": "lock_system_structure",
            "timestamp": datetime.now().isoformat(),
            "result": lock_config
        })
        
        self._save()
        
        return lock_config
    
    def get_compression_status(self) -> Dict[str, Any]:
        """获取压缩状态"""
        lock_file = os.path.join(self.storage_path, "structure_lock.json")
        is_locked = os.path.exists(lock_file)
        
        mutation_surface = self.policy_surface.get_mutation_surface()
        
        return {
            "is_locked": is_locked,
            "compression_steps": len(self.compression_history),
            "allowed_mutations": mutation_surface["allowed"],
            "forbidden_mutations": mutation_surface["forbidden"],
            "core_loop_stages": self.path_merger.get_core_loop(),
            "max_branching": self.graph_simplifier.max_branching,
            "max_depth": self.graph_simplifier.max_depth
        }
    
    def reset_compression(self) -> bool:
        """重置压缩（谨慎使用）"""
        lock_file = os.path.join(self.storage_path, "structure_lock.json")
        if os.path.exists(lock_file):
            os.remove(lock_file)
        
        self.compression_history.append({
            "action": "reset_compression",
            "timestamp": datetime.now().isoformat()
        })
        
        self._save()
        return True


def create_system_compressor() -> SystemCompressor:
    """工厂函数"""
    return SystemCompressor()

__exports__ = ['CoreLoopConfig', 'DecisionGraphSimplifier', 'MutationPermission', 'PathMerger', 'PathType', 'PolicyMutationSurface', 'SystemCompressor', 'UnifiedPath', 'create_system_compressor']


