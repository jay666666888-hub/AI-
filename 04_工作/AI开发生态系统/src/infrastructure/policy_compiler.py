#!/usr/bin/env python3
"""
Policy Compiler - 策略编译器
关键升级: 将 runtime eval 的 policy 编译为 execution graph

policy → compiled execution graph

编译后的执行图:
- 可预测执行路径
- 可验证约束
- 可静态分析
- 可提前预判冲突
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib


class NodeType(Enum):
    """图节点类型"""
    CONDITION = "condition"      # 条件判断
    ACTION = "action"            # 执行动作
    UTILITY_CHECK = "utility_check"  # 效用检查
    GOVERNOR_CHECK = "governor_check"  # Governor检查
    POLICY_UPDATE = "policy_update"    # 策略更新
    GOAL_SELECT = "goal_select"        # 目标选择
    MERGE = "merge"                    # 路径合并


class EdgeType(Enum):
    """图边类型"""
    TRUE = "true"          # 条件为真
    FALSE = "false"         # 条件为假
    SUCCESS = "success"     # 执行成功
    FAILURE = "failure"     # 执行失败
    PARTIAL = "partial"     # 部分成功
    ALWAYS = "always"       # 无条件


@dataclass
class CompiledNode:
    """编译后的图节点"""
    node_id: str
    node_type: NodeType
    
    # 节点内容
    label: str                    # 节点标签
    condition: Optional[str]       # 条件 (对于 CONDITION)
    action_fn: Optional[str]        # 动作函数名
    utility_threshold: Optional[float]  # 效用阈值
    governor_constraints: List[str]   # Governor约束列表
    
    # 元数据
    metadata: Dict[str, Any]
    
    # 编译信息
    compiled_at: str
    source_policy_version: str


@dataclass
class CompiledEdge:
    """编译后的图边"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    guard: Optional[str]      # 守卫条件
    weight: float            # 权重


@dataclass
class ExecutionGraph:
    """编译后的执行图"""
    graph_id: str
    name: str
    version: str
    
    nodes: List[CompiledNode]
    edges: List[CompiledEdge]
    
    entry_node_id: str        # 入口节点
    exit_nodes: List[str]     # 出口节点 (可能有多个)
    
    # 编译信息
    compiled_at: str
    source_policies: Dict[str, str]  # 源策略版本
    constraints_validated: bool
    
    # 统计
    node_count: int
    edge_count: int
    max_depth: int


@dataclass
class PolicyRule:
    """策略规则"""
    rule_id: str
    condition: str             # 条件表达式
    action: str                # 动作
    utility_weight: float      # 效用权重
    priority: int             # 优先级
    constraints: List[str]    # 约束列表


class PolicyCompiler:
    """
    Policy Compiler - 策略编译器
    
    将运行时评估的 policy 编译为可执行的图
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/compiled_policies"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.compiled_graphs: Dict[str, ExecutionGraph] = {}
        self.policy_rules: Dict[str, List[PolicyRule]] = {}
    
    def compile_policy(self,
                      policy_name: str,
                      policy_rules: List[PolicyRule],
                      version: str = "1.0") -> ExecutionGraph:
        """
        编译策略为执行图
        
        Args:
            policy_name: 策略名称
            policy_rules: 策略规则列表
            version: 版本
        
        Returns:
            ExecutionGraph
        """
        graph_id = f"graph_{policy_name}_{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        nodes = []
        edges = []
        
        # 创建入口节点
        entry_node = CompiledNode(
            node_id=f"{graph_id}_entry",
            node_type=NodeType.CONDITION,
            label=f"{policy_name}_start",
            condition=None,
            action_fn=None,
            utility_threshold=None,
            governor_constraints=[],
            metadata={},
            compiled_at=datetime.now().isoformat(),
            source_policy_version=version
        )
        nodes.append(entry_node)
        
        # 跟踪分支
        active_nodes = [entry_node.node_id]
        all_exit_nodes = []
        
        for rule in sorted(policy_rules, key=lambda r: r.priority):
            # 为每个规则创建: Condition → Action → UtilityCheck → GovernorCheck
            
            # 1. Condition Node
            cond_node = CompiledNode(
                node_id=f"{graph_id}_cond_{rule.rule_id}",
                node_type=NodeType.CONDITION,
                label=f"check_{rule.rule_id}",
                condition=rule.condition,
                action_fn=None,
                utility_threshold=None,
                governor_constraints=[],
                metadata={"rule_id": rule.rule_id, "priority": rule.priority},
                compiled_at=datetime.now().isoformat(),
                source_policy_version=version
            )
            nodes.append(cond_node)
            
            # 连接到活跃节点
            for src_id in active_nodes:
                edges.append(CompiledEdge(
                    edge_id=f"{graph_id}_e_{len(edges)}",
                    source_id=src_id,
                    target_id=cond_node.node_id,
                    edge_type=EdgeType.ALWAYS,
                    guard=None,
                    weight=1.0
                ))
            
            # 2. Action Node (True分支)
            action_node = CompiledNode(
                node_id=f"{graph_id}_action_{rule.rule_id}",
                node_type=NodeType.ACTION,
                label=f"execute_{rule.rule_id}",
                condition=None,
                action_fn=rule.action,
                utility_threshold=None,
                governor_constraints=rule.constraints,
                metadata={"rule_id": rule.rule_id, "utility_weight": rule.utility_weight},
                compiled_at=datetime.now().isoformat(),
                source_policy_version=version
            )
            nodes.append(action_node)
            
            # Cond → Action (True)
            edges.append(CompiledEdge(
                edge_id=f"{graph_id}_e_{len(edges)}",
                source_id=cond_node.node_id,
                target_id=action_node.node_id,
                edge_type=EdgeType.TRUE,
                guard=rule.condition,
                weight=rule.utility_weight
            ))
            
            # 3. Utility Check Node
            utility_node = CompiledNode(
                node_id=f"{graph_id}_util_{rule.rule_id}",
                node_type=NodeType.UTILITY_CHECK,
                label=f"utility_check_{rule.rule_id}",
                condition=None,
                action_fn=None,
                utility_threshold=0.2,  # 默认阈值
                governor_constraints=[],
                metadata={"rule_id": rule.rule_id, "threshold": 0.2},
                compiled_at=datetime.now().isoformat(),
                source_policy_version=version
            )
            nodes.append(utility_node)
            
            # Action → Utility (Success)
            edges.append(CompiledEdge(
                edge_id=f"{graph_id}_e_{len(edges)}",
                source_id=action_node.node_id,
                target_id=utility_node.node_id,
                edge_type=EdgeType.SUCCESS,
                guard=None,
                weight=1.0
            ))
            
            # 4. Governor Check Node
            gov_node = CompiledNode(
                node_id=f"{graph_id}_gov_{rule.rule_id}",
                node_type=NodeType.GOVERNOR_CHECK,
                label=f"governor_check_{rule.rule_id}",
                condition=None,
                action_fn=None,
                utility_threshold=None,
                governor_constraints=rule.constraints,
                metadata={"rule_id": rule.rule_id, "constraints": rule.constraints},
                compiled_at=datetime.now().isoformat(),
                source_policy_version=version
            )
            nodes.append(gov_node)
            
            # Utility → Governor (Success)
            edges.append(CompiledEdge(
                edge_id=f"{graph_id}_e_{len(edges)}",
                source_id=utility_node.node_id,
                target_id=gov_node.node_id,
                edge_type=EdgeType.SUCCESS,
                guard=None,
                weight=1.0
            ))
            
            # Exit节点
            exit_node = CompiledNode(
                node_id=f"{graph_id}_exit_{rule.rule_id}",
                node_type=NodeType.MERGE,
                label=f"{policy_name}_complete_{rule.rule_id}",
                condition=None,
                action_fn=None,
                utility_threshold=None,
                governor_constraints=[],
                metadata={"rule_id": rule.rule_id, "is_exit": True},
                compiled_at=datetime.now().isoformat(),
                source_policy_version=version
            )
            nodes.append(exit_node)
            all_exit_nodes.append(exit_node.node_id)
            
            # Governor → Exit (ALLOW)
            edges.append(CompiledEdge(
                edge_id=f"{graph_id}_e_{len(edges)}",
                source_id=gov_node.node_id,
                target_id=exit_node.node_id,
                edge_type=EdgeType.SUCCESS,
                guard=None,
                weight=1.0
            ))
            
            # 更新活跃节点为 exit
            active_nodes = [exit_node.node_id]
        
        # 计算最大深度
        max_depth = max(n.depth for n in nodes) if nodes else 0
        
        # 构建执行图
        graph = ExecutionGraph(
            graph_id=graph_id,
            name=policy_name,
            version=version,
            nodes=nodes,
            edges=edges,
            entry_node_id=entry_node.node_id,
            exit_nodes=all_exit_nodes,
            compiled_at=datetime.now().isoformat(),
            source_policies={policy_name: version},
            constraints_validated=self._validate_constraints(nodes, edges),
            node_count=len(nodes),
            edge_count=len(edges),
            max_depth=max_depth
        )
        
        self.compiled_graphs[graph_id] = graph
        self._save_graph(graph)
        
        return graph
    
    def _validate_constraints(self, nodes: List[CompiledNode], edges: List[CompiledEdge]) -> bool:
        """验证约束一致性"""
        # 检查所有 Governor Check 节点的约束是否在之前定义
        gov_nodes = [n for n in nodes if n.node_type == NodeType.GOVERNOR_CHECK]
        
        for gov_node in gov_nodes:
            constraints = gov_node.governor_constraints
            # 简化验证: 检查约束是否非空
            if not constraints:
                return False
        
        return True
    
    def _save_graph(self, graph: ExecutionGraph):
        """保存编译图"""
        graph_file = os.path.join(self.storage_path, f"{graph.graph_id}.json")
        
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump({
                "graph_id": graph.graph_id,
                "name": graph.name,
                "version": graph.version,
                "entry_node_id": graph.entry_node_id,
                "exit_nodes": graph.exit_nodes,
                "compiled_at": graph.compiled_at,
                "source_policies": graph.source_policies,
                "constraints_validated": graph.constraints_validated,
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
                "max_depth": graph.max_depth,
                "nodes": [{
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "label": n.label,
                    "condition": n.condition,
                    "action_fn": n.action_fn,
                    "utility_threshold": n.utility_threshold,
                    "governor_constraints": n.governor_constraints,
                    "metadata": n.metadata,
                    "compiled_at": n.compiled_at,
                    "source_policy_version": n.source_policy_version
                } for n in graph.nodes],
                "edges": [{
                    "edge_id": e.edge_id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type.value,
                    "guard": e.guard,
                    "weight": e.weight
                } for e in graph.edges]
            }, f, ensure_ascii=False, indent=2)
    
    def load_graph(self, graph_id: str) -> Optional[ExecutionGraph]:
        """加载编译图"""
        graph_file = os.path.join(self.storage_path, f"{graph_id}.json")
        
        if not os.path.exists(graph_file):
            return None
        
        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = [CompiledNode(
                node_id=n["node_id"],
                node_type=NodeType(n["node_type"]),
                label=n["label"],
                condition=n["condition"],
                action_fn=n["action_fn"],
                utility_threshold=n["utility_threshold"],
                governor_constraints=n["governor_constraints"],
                metadata=n["metadata"],
                compiled_at=n["compiled_at"],
                source_policy_version=n["source_policy_version"]
            ) for n in data["nodes"]]
            
            edges = [CompiledEdge(
                edge_id=e["edge_id"],
                source_id=e["source_id"],
                target_id=e["target_id"],
                edge_type=EdgeType(e["edge_type"]),
                guard=e["guard"],
                weight=e["weight"]
            ) for e in data["edges"]]
            
            return ExecutionGraph(
                graph_id=data["graph_id"],
                name=data["name"],
                version=data["version"],
                nodes=nodes,
                edges=edges,
                entry_node_id=data["entry_node_id"],
                exit_nodes=data["exit_nodes"],
                compiled_at=data["compiled_at"],
                source_policies=data["source_policies"],
                constraints_validated=data["constraints_validated"],
                node_count=data["node_count"],
                edge_count=data["edge_count"],
                max_depth=data["max_depth"]
            )
        except:
            return None
    
    def get_executable_path(self, graph: ExecutionGraph, context: Dict[str, Any]) -> List[str]:
        """
        获取可执行路径
        
        根据上下文, 预测执行路径
        """
        path = [graph.entry_node_id]
        current_node_id = graph.entry_node_id
        
        max_iterations = graph.node_count * 2  # 防止无限循环
        iterations = 0
        
        while current_node_id not in graph.exit_nodes and iterations < max_iterations:
            next_edge = self._find_next_edge(graph, current_node_id, context)
            
            if not next_edge:
                break
            
            path.append(next_edge.target_id)
            current_node_id = next_edge.target_id
            iterations += 1
        
        return path
    
    def _find_next_edge(self, graph: ExecutionGraph, node_id: str, context: Dict[str, Any]) -> Optional[CompiledEdge]:
        """找到下一个满足条件的边"""
        outgoing_edges = [e for e in graph.edges if e.source_id == node_id]
        
        if not outgoing_edges:
            return None
        
        # 优先找 True 分支
        true_edges = [e for e in outgoing_edges if e.edge_type == EdgeType.TRUE]
        
        for edge in true_edges:
            if self._check_guard(edge.guard, context):
                return edge
        
        # 其次找 ALWAYS
        always_edges = [e for e in outgoing_edges if e.edge_type == EdgeType.ALWAYS]
        if always_edges:
            return always_edges[0]
        
        # 最后找 SUCCESS
        success_edges = [e for e in outgoing_edges if e.edge_type == EdgeType.SUCCESS]
        if success_edges:
            return success_edges[0]
        
        return outgoing_edges[0] if outgoing_edges else None
    
    def _check_guard(self, guard: Optional[str], context: Dict[str, Any]) -> bool:
        """检查守卫条件"""
        if not guard:
            return True
        
        # 简化: 直接检查 context 中是否有对应值
        # 实际实现需要更复杂的表达式解析
        try:
            return guard in context and context[guard]
        except:
            return False
    
    def analyze_graph(self, graph: ExecutionGraph) -> Dict[str, Any]:
        """分析执行图"""
        node_types = {}
        for node in graph.nodes:
            type_name = node.node_type.value
            node_types[type_name] = node_types.get(type_name, 0) + 1
        
        # 找出关键路径 (最长路径)
        longest_path = self._find_longest_path(graph)
        
        # 约束覆盖率
        all_constraints = set()
        for node in graph.nodes:
            all_constraints.update(node.governor_constraints)
        
        return {
            "graph_id": graph.graph_id,
            "name": graph.name,
            "version": graph.version,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "max_depth": graph.max_depth,
            "node_types": node_types,
            "constraints_count": len(all_constraints),
            "constraints_validated": graph.constraints_validated,
            "longest_path": longest_path,
            "entry": graph.entry_node_id,
            "exits": graph.exit_nodes
        }
    
    def _find_longest_path(self, graph: ExecutionGraph) -> List[str]:
        """找到最长路径"""
        # 简单的 DFS 找最长路径
        def dfs(node_id: str, visited: Set[str], path: List[str]) -> List[str]:
            if node_id in visited or node_id in graph.exit_nodes:
                return path
            
            visited.add(node_id)
            path = path + [node_id]
            
            outgoing = [e.target_id for e in graph.edges if e.source_id == node_id]
            
            best_path = path
            for next_id in outgoing:
                result = dfs(next_id, visited.copy(), path.copy())
                if len(result) > len(best_path):
                    best_path = result
            
            return best_path
        
        return dfs(graph.entry_node_id, set(), [])
    
    def get_compiled_graphs(self) -> List[str]:
        """获取所有编译图ID"""
        return list(self.compiled_graphs.keys())


def create_policy_compiler() -> PolicyCompiler:
    """工厂函数"""
    return PolicyCompiler()

__exports__ = ['CompiledEdge', 'CompiledNode', 'EdgeType', 'ExecutionGraph', 'NodeType', 'PolicyCompiler', 'PolicyRule', 'create_policy_compiler']


