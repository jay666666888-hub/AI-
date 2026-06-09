#!/usr/bin/env python3
"""
Execution Trace System - 执行追踪系统
核心功能:
- Full decision replay (完整决策回放)
- Causal graph (因果图)
- Why-this-decision-happened (为什么做出这个决策)

这是 debug / research 的核心组件
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import hashlib


class TraceNodeType(Enum):
    """追踪节点类型"""
    ACTION = "action"
    DECISION = "decision"
    GOVERNANCE = "governance"
    UTILITY = "utility"
    POLICY_UPDATE = "policy_update"
    GOAL = "goal"
    SKILL = "skill"
    AGENT = "agent"
    ERROR = "error"
    ROLLBACK = "rollback"


@dataclass
class TraceNode:
    """追踪节点"""
    node_id: str
    node_type: TraceNodeType
    timestamp: str
    
    # 节点内容
    action: str              # 执行的动作
    input_data: Dict[str, Any]   # 输入数据
    output_data: Dict[str, Any]   # 输出数据
    result: str              # result: success/failure/partial
    
    # 因果关系
    parent_nodes: List[str]  # 父节点 (原因)
    child_nodes: List[str]   # 子节点 (结果)
    
    # 决策上下文
    context: Dict[str, Any]  # 决策上下文
    reasoning: str           # 推理过程
    constraints_checked: List[str]  # 检查的约束
    
    # 元数据
    depth: int              # 深度
    duration_ms: int         # 执行时长
    metadata: Dict[str, Any]


@dataclass
class CausalEdge:
    """因果边"""
    edge_id: str
    source_node: str
    target_node: str
    edge_type: str          # "causes", "enables", "blocks", "modifies"
    weight: float            # 权重 (因果强度)
    description: str


@dataclass
class DecisionReplay:
    """决策回放"""
    trace_id: str
    root_node_id: str
    nodes: List[TraceNode]
    edges: List[CausalEdge]
    start_time: str
    end_time: str
    duration_ms: int
    outcome: str             # success/failure/partial
    key_decisions: List[str]  # 关键决策节点


class ExecutionTracer:
    """
    Execution Tracer - 执行追踪器
    
    记录所有执行过程, 构建因果图
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/traces"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.current_trace: List[TraceNode] = []
        self.current_edges: List[CausalEdge] = []
        self.node_index: Dict[str, TraceNode] = {}
        
        self.traces: List[str] = []  # trace IDs
    
    def start_trace(self, trace_id: str = None) -> str:
        """开始一个新的追踪"""
        trace_id = trace_id or f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.current_trace = []
        self.current_edges = []
        self.node_index = {}
        
        return trace_id
    
    def add_node(self,
                node_type: TraceNodeType,
                action: str,
                input_data: Dict[str, Any],
                output_data: Dict[str, Any],
                result: str,
                reasoning: str = "",
                context: Dict[str, Any] = None,
                parent_node_ids: List[str] = None,
                metadata: Dict[str, Any] = None) -> str:
        """
        添加追踪节点
        
        Args:
            node_type: 节点类型
            action: 执行的动作
            input_data: 输入数据
            output_data: 输出数据
            result: 结果
            reasoning: 推理过程
            context: 上下文
            parent_node_ids: 父节点 (原因)
            metadata: 元数据
        
        Returns:
            node_id
        """
        node_id = str(uuid.uuid4())[:12]
        
        # 深度 = 最大父节点深度 + 1
        depth = 0
        if parent_node_ids:
            depths = [self.node_index[pid].depth for pid in parent_node_ids if pid in self.node_index]
            if depths:
                depth = max(depths) + 1
        
        node = TraceNode(
            node_id=node_id,
            node_type=node_type,
            timestamp=datetime.now().isoformat(),
            action=action,
            input_data=input_data,
            output_data=output_data,
            result=result,
            parent_nodes=parent_node_ids or [],
            child_nodes=[],
            context=context or {},
            reasoning=reasoning,
            constraints_checked=context.get("constraints_checked", []) if context else [],
            depth=depth,
            duration_ms=metadata.get("duration_ms", 0) if metadata else 0,
            metadata=metadata or {}
        )
        
        self.current_trace.append(node)
        self.node_index[node_id] = node
        
        # 更新子节点引用
        if parent_node_ids:
            for pid in parent_node_ids:
                if pid in self.node_index:
                    parent = self.node_index[pid]
                    if node_id not in parent.child_nodes:
                        parent.child_nodes.append(node_id)
        
        return node_id
    
    def add_causal_edge(self,
                       source_node: str,
                       target_node: str,
                       edge_type: str = "causes",
                       weight: float = 1.0,
                       description: str = "") -> str:
        """添加因果边"""
        edge_id = str(uuid.uuid4())[:8]
        
        edge = CausalEdge(
            edge_id=edge_id,
            source_node=source_node,
            target_node=target_node,
            edge_type=edge_type,
            weight=weight,
            description=description
        )
        
        self.current_edges.append(edge)
        return edge_id
    
    def end_trace(self, outcome: str = "success") -> DecisionReplay:
        """结束追踪并生成回放"""
        if not self.current_trace:
            return None
        
        start_time = self.current_trace[0].timestamp
        end_time = self.current_trace[-1].timestamp
        
        # 计算时长
        try:
            from datetime import datetime as dt
            start = dt.fromisoformat(start_time)
            end = dt.fromisoformat(end_time)
            duration_ms = int((end - start).total_seconds() * 1000)
        except:
            duration_ms = 0
        
        # 找关键决策节点
        key_decisions = [
            n.node_id for n in self.current_trace
            if n.node_type in [TraceNodeType.DECISION, TraceNodeType.GOVERNANCE]
        ]
        
        # 生成回放
        replay = DecisionReplay(
            trace_id=f"replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            root_node_id=self.current_trace[0].node_id,
            nodes=self.current_trace.copy(),
            edges=self.current_edges.copy(),
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            outcome=outcome,
            key_decisions=key_decisions
        )
        
        self._save_replay(replay)
        self.traces.append(replay.trace_id)
        
        return replay
    
    def _save_replay(self, replay: DecisionReplay):
        """保存回放到文件"""
        replay_file = os.path.join(self.storage_path, f"{replay.trace_id}.json")
        
        with open(replay_file, 'w', encoding='utf-8') as f:
            json.dump({
                "trace_id": replay.trace_id,
                "root_node_id": replay.root_node_id,
                "start_time": replay.start_time,
                "end_time": replay.end_time,
                "duration_ms": replay.duration_ms,
                "outcome": replay.outcome,
                "key_decisions": replay.key_decisions,
                "nodes": [{
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "timestamp": n.timestamp,
                    "action": n.action,
                    "input_data": n.input_data,
                    "output_data": n.output_data,
                    "result": n.result,
                    "parent_nodes": n.parent_nodes,
                    "child_nodes": n.child_nodes,
                    "context": n.context,
                    "reasoning": n.reasoning,
                    "constraints_checked": n.constraints_checked,
                    "depth": n.depth,
                    "duration_ms": n.duration_ms,
                    "metadata": n.metadata
                } for n in replay.nodes],
                "edges": [{
                    "edge_id": e.edge_id,
                    "source_node": e.source_node,
                    "target_node": e.target_node,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                    "description": e.description
                } for e in replay.edges]
            }, f, ensure_ascii=False, indent=2)
    
    def get_trace(self, trace_id: str) -> Optional[DecisionReplay]:
        """获取追踪回放"""
        replay_file = os.path.join(self.storage_path, f"{trace_id}.json")
        
        if not os.path.exists(replay_file):
            return None
        
        try:
            with open(replay_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            nodes = [TraceNode(
                node_id=n["node_id"],
                node_type=TraceNodeType(n["node_type"]),
                timestamp=n["timestamp"],
                action=n["action"],
                input_data=n["input_data"],
                output_data=n["output_data"],
                result=n["result"],
                parent_nodes=n["parent_nodes"],
                child_nodes=n["child_nodes"],
                context=n["context"],
                reasoning=n["reasoning"],
                constraints_checked=n["constraints_checked"],
                depth=n["depth"],
                duration_ms=n["duration_ms"],
                metadata=n["metadata"]
            ) for n in data["nodes"]]
            
            edges = [CausalEdge(
                edge_id=e["edge_id"],
                source_node=e["source_node"],
                target_node=e["target_node"],
                edge_type=e["edge_type"],
                weight=e["weight"],
                description=e["description"]
            ) for e in data["edges"]]
            
            return DecisionReplay(
                trace_id=data["trace_id"],
                root_node_id=data["root_node_id"],
                nodes=nodes,
                edges=edges,
                start_time=data["start_time"],
                end_time=data["end_time"],
                duration_ms=data["duration_ms"],
                outcome=data["outcome"],
                key_decisions=data["key_decisions"]
            )
        except:
            return None
    
    def explain_decision(self, node_id: str) -> Dict[str, Any]:
        """
        解释一个决策 (Why-this-decision-happened)
        
        Returns:
            决策原因链
        """
        if node_id not in self.node_index:
            return {"error": "node not found"}
        
        node = self.node_index[node_id]
        
        # 追溯父节点 (原因链)
        causes = []
        for parent_id in node.parent_nodes:
            if parent_id in self.node_index:
                parent = self.node_index[parent_id]
                causes.append({
                    "node_id": parent_id,
                    "action": parent.action,
                    "reasoning": parent.reasoning,
                    "result": parent.result
                })
        
        # 查看子节点 (影响链)
        effects = []
        for child_id in node.child_nodes:
            if child_id in self.node_index:
                child = self.node_index[child_id]
                effects.append({
                    "node_id": child_id,
                    "action": child.action,
                    "result": child.result
                })
        
        return {
            "target_node": {
                "node_id": node_id,
                "action": node.action,
                "reasoning": node.reasoning,
                "result": node.result,
                "constraints_checked": node.constraints_checked
            },
            "causes": causes,      # 为什么发生
            "effects": effects,     # 导致什么
            "depth": node.depth,
            "timestamp": node.timestamp
        }
    
    def get_causal_graph(self, trace_id: str = None) -> Dict[str, Any]:
        """
        获取因果图
        
        Returns:
            {
                "nodes": [...],
                "edges": [...]
            }
        """
        if trace_id:
            replay = self.get_trace(trace_id)
            if not replay:
                return {}
            nodes = replay.nodes
            edges = replay.edges
        else:
            nodes = self.current_trace
            edges = self.current_edges
        
        return {
            "nodes": [{
                "id": n.node_id,
                "type": n.node_type.value,
                "action": n.action,
                "depth": n.depth,
                "result": n.result
            } for n in nodes],
            "edges": [{
                "source": e.source_node,
                "target": e.target_node,
                "type": e.edge_type,
                "weight": e.weight
            } for e in edges]
        }
    
    def get_recent_traces(self, limit: int = 10) -> List[str]:
        """获取最近的追踪ID"""
        all_traces = []
        for fname in os.listdir(self.storage_path):
            if fname.endswith(".json"):
                all_traces.append(fname[:-5])
        
        return sorted(all_traces, reverse=True)[:limit]


def create_execution_tracer() -> ExecutionTracer:
    """工厂函数"""
    return ExecutionTracer()

__exports__ = ['CausalEdge', 'DecisionReplay', 'ExecutionTracer', 'TraceNode', 'TraceNodeType', 'create_execution_tracer']


