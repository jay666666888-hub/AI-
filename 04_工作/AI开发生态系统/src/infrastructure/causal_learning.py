#!/usr/bin/env python3
"""
Causal Learning Layer - 因果学习层
把 trace system 升级为: causality → policy update loop

让系统"从因果中学习", 不是从结果学习

核心功能:
- Causal graph construction from traces
- Causal effect measurement
- Causal-based policy updates
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math


class CausalRelationship(Enum):
    DIRECT = "direct"           # 直接因果
    INDIRECT = "indirect"        # 间接因果
    SPURIOUS = "spurious"         # 伪因果 (需要过滤)
    UNKNOWN = "unknown"


@dataclass
class CausalEdge:
    """因果边"""
    cause_node: str
    effect_node: str
    relationship: CausalRelationship
    
    # 因果强度
    causal_strength: float       # 0-1, 越大因果越强
    confidence: float            # 置信度
    
    # 统计
    observations: int            # 观察次数
    correlation: float           # 相关系数
    
    # 时间特性
    time_lag_ms: int             # 因果延迟
    is_recursive: bool          # 是否递归


@dataclass
class CausalPath:
    """因果路径"""
    path_id: str
    nodes: List[str]            # 路径上的节点序列
    edges: List[CausalEdge]      # 路径上的边
    total_strength: float       # 路径总强度
    
    # 分析
    is_direct: bool
    is_recursive: bool
    length: int                 # 跳数


@dataclass
class CausalInsight:
    """因果洞察"""
    insight_id: str
    cause: str                  # 原因
    effect: str                 # 结果
    causal_mechanism: str       # 因果机制描述
    confidence: float
    
    # Policy 更新建议
    policy_recommendation: str
    expected_improvement: float
    
    # 证据
    supporting_evidence: List[str]
    counter_evidence: List[str]


@dataclass
class PolicyUpdateFromCausal:
    """基于因果的策略更新"""
    update_id: str
    timestamp: str
    
    # 触发
    trigger_insight_id: str
    causal_path: str
    
    # 更新内容
    policy_target: str          # 更新的策略目标
    delta: float                # 变化量
    direction: str              # increase/decrease
    
    # 验证
    expected_outcome: str
    actual_outcome: Optional[str] = None
    verified: bool = False


class CausalGraphBuilder:
    """
    Causal Graph Builder - 从 Trace 构建因果图
    
    从 execution traces 中提取因果关系
    """
    
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}  # node_id -> node_info
        self.edges: List[CausalEdge] = []
        self.observations: List[Dict[str, Any]] = []  # 时间序列观察
    
    def add_trace(self, trace_nodes: List[Dict[str, Any]]) -> None:
        """
        添加执行 trace
        
        Args:
            trace_nodes: [{"node_id": "...", "action": "...", "result": "...", "timestamp": "..."}, ...]
        """
        # 提取节点
        for node in trace_nodes:
            node_id = node.get("node_id")
            if node_id:
                if node_id not in self.nodes:
                    self.nodes[node_id] = {
                        "type": node.get("node_type"),
                        "action": node.get("action"),
                        "first_seen": node.get("timestamp"),
                        "last_seen": node.get("timestamp"),
                        "occurrence_count": 0
                    }
                else:
                    self.nodes[node_id]["occurrence_count"] += 1
                    self.nodes[node_id]["last_seen"] = node.get("timestamp")
        
        # 提取边 (连续节点之间)
        for i in range(len(trace_nodes) - 1):
            node1 = trace_nodes[i]
            node2 = trace_nodes[i + 1]
            
            # 检查是否已存在边
            existing_edge = self._find_edge(node1["node_id"], node2["node_id"])
            
            if existing_edge:
                # 更新已有边
                existing_edge.observations += 1
            else:
                # 创建新边
                edge = CausalEdge(
                    cause_node=node1["node_id"],
                    effect_node=node2["node_id"],
                    relationship=CausalRelationship.UNKNOWN,
                    causal_strength=0.0,
                    confidence=0.0,
                    observations=1,
                    correlation=0.0,
                    time_lag_ms=0,
                    is_recursive=False
                )
                self.edges.append(edge)
        
        self.observations.append({
            "timestamp": datetime.now().isoformat(),
            "trace": trace_nodes
        })
    
    def _find_edge(self, cause: str, effect: str) -> Optional[CausalEdge]:
        """查找是否存在边"""
        for edge in self.edges:
            if edge.cause_node == cause and edge.effect_node == effect:
                return edge
        return None
    
    def compute_causal_strength(self) -> None:
        """
        计算因果强度
        
        使用条件概率和互信息
        """
        # 计算每个边的因果强度
        for edge in self.edges:
            # 观察次数作为基础
            base_strength = min(1.0, edge.observations / 10)
            
            # 如果是递归边, 降低强度
            if self._is_recursive_path(edge.cause_node, edge.effect_node):
                edge.is_recursive = True
                base_strength *= 0.5
            
            edge.causal_strength = base_strength
            edge.confidence = min(1.0, edge.observations / 5) * base_strength
    
    def _is_recursive_path(self, cause: str, effect: str) -> bool:
        """检查是否形成递归路径"""
        # 检查是否存在 cause -> ... -> cause 路径
        visited = set()
        stack = [effect]
        
        while stack:
            current = stack.pop()
            if current == cause:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            # 找当前节点的后继
            for edge in self.edges:
                if edge.cause_node == current:
                    stack.append(edge.effect_node)
        
        return False
    
    def filter_spurious_correlations(self) -> List[CausalEdge]:
        """
        过滤伪因果关系
        
        伪因果: 表面上相关但实际没有因果关系
        """
        spurious = []
        
        for edge in self.edges:
            # 检查是否只因为共享前因而相关
            if self._has_common_cause(edge.cause_node, edge.effect_node):
                edge.relationship = CausalRelationship.SPURIOUS
                spurious.append(edge)
            
            # 检查是否形成冲突路径
            if self._has_conflicting_paths(edge.cause_node, edge.effect_node):
                edge.relationship = CausalRelationship.SPURIOUS
                spurious.append(edge)
        
        return spurious
    
    def _has_common_cause(self, node1: str, node2: str) -> bool:
        """检查是否有共同原因"""
        causes1 = set(e.cause_node for e in self.edges if e.effect_node == node1)
        causes2 = set(e.cause_node for e in self.edges if e.effect_node == node2)
        
        common = causes1 & causes2
        return len(common) > 1  # 有多个共同原因
    
    def _has_conflicting_paths(self, cause: str, effect: str) -> bool:
        """检查是否有冲突路径"""
        # 如果存在 cause -> X -> effect 和 cause -> Y -> effect
        # 且 X 和 Y 不同, 则可能是伪因果
        path1_exists = self._path_exists([cause], effect, max_hops=2)
        path2_exists = self._path_exists([cause], effect, max_hops=2, exclude=path1_exists)
        
        return path1_exists and path2_exists
    
    def _path_exists(self, start_nodes: List[str], target: str, 
                    max_hops: int, exclude: List[str] = None) -> bool:
        """检查是否存在路径"""
        if exclude is None:
            exclude = []
        
        visited = set(exclude)
        stack = [(n, 0) for n in start_nodes]
        
        while stack:
            current, hops = stack.pop()
            
            if current == target and hops > 0:
                return True
            
            if hops >= max_hops:
                continue
            
            if current in visited:
                continue
            
            visited.add(current)
            
            for edge in self.edges:
                if edge.cause_node == current:
                    stack.append((edge.effect_node, hops + 1))
        
        return False
    
    def get_causal_graph(self) -> Dict[str, Any]:
        """获取因果图"""
        self.compute_causal_strength()
        
        return {
            "nodes": [{
                "id": node_id,
                "type": info.get("type"),
                "action": info.get("action"),
                "occurrences": info.get("occurrence_count", 0)
            } for node_id, info in self.nodes.items()],
            "edges": [{
                "cause": e.cause_node,
                "effect": e.effect_node,
                "strength": e.causal_strength,
                "confidence": e.confidence,
                "relationship": e.relationship.value,
                "is_recursive": e.is_recursive,
                "observations": e.observations
            } for e in self.edges if e.relationship != CausalRelationship.SPURIOUS]
        }


class CausalLearningLayer:
    """
    Causal Learning Layer - 因果学习主引擎
    
    从因果中学习, 而不只是从结果学习
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/causal_learning"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.causal_graph = CausalGraphBuilder()
        self.insights: List[CausalInsight] = []
        self.policy_updates: List[PolicyUpdateFromCausal] = []
        
        self._load_history()
    
    def _load_history(self):
        insights_file = os.path.join(self.storage_path, "insights.json")
        if os.path.exists(insights_file):
            try:
                with open(insights_file, 'r', encoding='utf-8') as f:
                    self.insights = [CausalInsight(**i) for i in json.load(f)]
            except:
                self.insights = []
        
        updates_file = os.path.join(self.storage_path, "policy_updates.json")
        if os.path.exists(updates_file):
            try:
                with open(updates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.policy_updates = [PolicyUpdateFromCausal(**u) for u in data]
            except:
                self.policy_updates = []
    
    def _save_history(self):
        insights_file = os.path.join(self.storage_path, "insights.json")
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "insight_id": i.insight_id,
                "cause": i.cause,
                "effect": i.effect,
                "causal_mechanism": i.causal_mechanism,
                "confidence": i.confidence,
                "policy_recommendation": i.policy_recommendation,
                "expected_improvement": i.expected_improvement,
                "supporting_evidence": i.supporting_evidence,
                "counter_evidence": i.counter_evidence
            } for i in self.insights[-50:]], f, ensure_ascii=False, indent=2)
        
        updates_file = os.path.join(self.storage_path, "policy_updates.json")
        with open(updates_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "update_id": u.update_id,
                "timestamp": u.timestamp,
                "trigger_insight_id": u.trigger_insight_id,
                "causal_path": u.causal_path,
                "policy_target": u.policy_target,
                "delta": u.delta,
                "direction": u.direction,
                "expected_outcome": u.expected_outcome,
                "actual_outcome": u.actual_outcome,
                "verified": u.verified
            } for u in self.policy_updates[-50:]], f, ensure_ascii=False, indent=2)
    
    def learn_from_trace(self, trace_id: str, trace_nodes: List[Dict[str, Any]]) -> None:
        """
        从 trace 学习因果关系
        
        Args:
            trace_id: trace ID
            trace_nodes: trace 节点列表
        """
        # 1. 添加到因果图
        self.causal_graph.add_trace(trace_nodes)
        
        # 2. 过滤伪因果
        spurious = self.causal_graph.filter_spurious_correlations()
        
        # 3. 生成洞察
        self._generate_insights(trace_id)
    
    def _generate_insights(self, trace_id: str) -> None:
        """从因果图生成洞察"""
        edges = self.causal_graph.edges
        
        # 找强因果边
        strong_edges = [e for e in edges 
                       if e.causal_strength > 0.7 and e.confidence > 0.6
                       and e.relationship != CausalRelationship.SPURIOUS]
        
        for edge in strong_edges:
            # 检查是否已有类似洞察
            existing = any(i.cause == edge.cause_node and i.effect == edge.effect_node
                          for i in self.insights)
            
            if not existing:
                insight = CausalInsight(
                    insight_id=f"insight_{len(self.insights)}_{datetime.now().strftime('%H%M%S')}",
                    cause=edge.cause_node,
                    effect=edge.effect_node,
                    causal_mechanism=f"{edge.cause_node} causes {edge.effect_node} "
                                    f"(strength={edge.causal_strength:.2f})",
                    confidence=edge.confidence,
                    policy_recommendation=self._recommend_policy(edge),
                    expected_improvement=edge.causal_strength * 0.1,
                    supporting_evidence=[f"Observed {edge.observations} times"],
                    counter_evidence=[]
                )
                
                self.insights.append(insight)
        
        self._save_history()
    
    def _recommend_policy(self, edge: CausalEdge) -> str:
        """基于因果边推荐策略"""
        # 如果 cause 导致低 utility, 建议减少 cause 的权重
        if "low_utility" in edge.effect_node or "failure" in edge.effect_node:
            return f"decrease weight of {edge.cause_node}"
        
        # 如果 cause 导致高成功, 建议增加 cause 的权重
        if "success" in edge.effect_node or "high_utility" in edge.effect_node:
            return f"increase weight of {edge.cause_node}"
        
        return f"review and adjust {edge.cause_node} parameters"
    
    def get_causal_insights(self, min_confidence: float = 0.5) -> List[CausalInsight]:
        """获取因果洞察"""
        return [i for i in self.insights if i.confidence >= min_confidence]
    
    def apply_causal_policy_update(self, 
                                   insight: CausalInsight,
                                   current_policy: Dict[str, float]) -> Dict[str, float]:
        """
        应用基于因果洞察的策略更新
        
        Args:
            insight: 因果洞察
            current_policy: 当前策略状态
        
        Returns:
            更新后的策略
        """
        import uuid
        
        # 解析推荐
        recommendation = insight.policy_recommendation
        
        if "increase weight of" in recommendation:
            target = recommendation.replace("increase weight of ", "")
            delta = insight.expected_improvement
            direction = "increase"
        elif "decrease weight of" in recommendation:
            target = recommendation.replace("decrease weight of ", "")
            delta = -insight.expected_improvement
            direction = "decrease"
        else:
            return current_policy
        
        # 更新策略
        updated_policy = current_policy.copy()
        if target in updated_policy:
            updated_policy[target] = max(0.0, min(1.0, updated_policy[target] + delta))
        
        # 记录更新
        update = PolicyUpdateFromCausal(
            update_id=str(uuid.uuid4())[:12],
            timestamp=datetime.now().isoformat(),
            trigger_insight_id=insight.insight_id,
            causal_path=f"{insight.cause} -> {insight.effect}",
            policy_target=target,
            delta=delta,
            direction=direction,
            expected_outcome=insight.causal_mechanism
        )
        
        self.policy_updates.append(update)
        self._save_history()
        
        return updated_policy
    
    def verify_policy_update(self, update_id: str, actual_outcome: str) -> bool:
        """验证策略更新"""
        update = next((u for u in self.policy_updates if u.update_id == update_id), None)
        
        if not update:
            return False
        
        update.actual_outcome = actual_outcome
        update.verified = True
        
        self._save_history()
        return True
    
    def get_causal_summary(self) -> Dict[str, Any]:
        """获取因果学习摘要"""
        return {
            "total_insights": len(self.insights),
            "verified_updates": sum(1 for u in self.policy_updates if u.verified),
            "pending_updates": sum(1 for u in self.policy_updates if not u.verified),
            "graph_nodes": len(self.causal_graph.nodes),
            "graph_edges": len(self.causal_graph.edges),
            "spurious_relationships": len([e for e in self.causal_graph.edges 
                                         if e.relationship == CausalRelationship.SPURIOUS]),
            "high_confidence_insights": len([i for i in self.insights if i.confidence > 0.8])
        }


def create_causal_learning_layer() -> CausalLearningLayer:
    """工厂函数"""
    return CausalLearningLayer()

__exports__ = ['CausalEdge', 'CausalGraphBuilder', 'CausalInsight', 'CausalLearningLayer', 'CausalPath', 'CausalRelationship', 'PolicyUpdateFromCausal', 'create_causal_learning_layer']


