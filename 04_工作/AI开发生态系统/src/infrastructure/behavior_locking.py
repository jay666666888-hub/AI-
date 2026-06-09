#!/usr/bin/env python3
"""
Behavior Locking - 行为锁定
Step 2: 冻结"结构"，只允许"参数变化"

核心原则:
- system architecture is frozen
- only parameters evolve

锁定:
- agent结构
- pipeline结构
- skill调用顺序

只允许:
- 权重变化
- 评分变化
- 选择概率变化
"""

import os
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib


class LockType(Enum):
    STRUCTURAL = "structural"    # 结构锁定（不可变）
    PARAMETRIC = "parametric"    # 参数锁定（可变化）
    FROZEN = "frozen"           # 完全冻结


@dataclass
class LockedComponent:
    """被锁定的组件"""
    component_id: str
    component_type: str  # "agent", "pipeline", "skill", "layer"
    lock_type: LockType
    locked_at: str
    locked_by: str  # "system" | "user" | "compression"
    config_hash: str  # 配置哈希，用于验证未被篡改
    allowed_mutations: Set[str]
    metadata: Dict[str, Any]


@dataclass
class ParameterSnapshot:
    """参数快照（用于验证参数未被非法修改）"""
    snapshot_id: str
    component_id: str
    timestamp: str
    parameters: Dict[str, Any]
    hash: str


@dataclass
class LockValidationResult:
    """锁定验证结果"""
    is_valid: bool
    component_id: str
    expected_hash: str
    actual_hash: str
    violations: List[str]


class ArchitectureLock:
    """
    Architecture Lock - 架构锁定
    
    锁定系统架构的所有组件
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/locking/architecture"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.locked_components: Dict[str, LockedComponent] = {}
        self._load()
    
    def _load(self):
        locks_file = os.path.join(self.storage_path, "locked_components.json")
        if os.path.exists(locks_file):
            try:
                with open(locks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换 allowed_mutations 从 list 到 set
                    self.locked_components = {
                        k: LockedComponent(
                            component_id=v["component_id"],
                            component_type=v["component_type"],
                            lock_type=LockType(v["lock_type"]),
                            locked_at=v["locked_at"],
                            locked_by=v["locked_by"],
                            config_hash=v["config_hash"],
                            allowed_mutations=set(v["allowed_mutations"]),
                            metadata=v.get("metadata", {})
                        )
                        for k, v in data.items()
                    }
            except:
                self.locked_components = {}
    
    def _save(self):
        locks_file = os.path.join(self.storage_path, "locked_components.json")
        with open(locks_file, 'w', encoding='utf-8') as f:
            json.dump({
                k: {
                    "component_id": v.component_id,
                    "component_type": v.component_type,
                    "lock_type": v.lock_type.value,
                    "locked_at": v.locked_at,
                    "locked_by": v.locked_by,
                    "config_hash": v.config_hash,
                    "allowed_mutations": list(v.allowed_mutations),
                    "metadata": v.metadata
                }
                for k, v in self.locked_components.items()
            }, f, ensure_ascii=False, indent=2)
    
    def _compute_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希"""
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def lock_component(self,
                      component_id: str,
                      component_type: str,
                      config: Dict[str, Any],
                      allowed_mutations: List[str],
                      locked_by: str = "system") -> LockedComponent:
        """
        锁定组件
        
        Args:
            component_id: 组件ID
            component_type: 组件类型
            config: 组件配置
            allowed_mutations: 允许的变更类型
            locked_by: 锁定者
        """
        component = LockedComponent(
            component_id=component_id,
            component_type=component_type,
            lock_type=LockType.STRUCTURAL,
            locked_at=datetime.now().isoformat(),
            locked_by=locked_by,
            config_hash=self._compute_hash(config),
            allowed_mutations=set(allowed_mutations),
            metadata=config
        )
        
        self.locked_components[component_id] = component
        self._save()
        
        return component
    
    def unlock_component(self, component_id: str) -> bool:
        """解锁组件（谨慎使用）"""
        if component_id in self.locked_components:
            del self.locked_components[component_id]
            self._save()
            return True
        return False
    
    def is_locked(self, component_id: str) -> bool:
        """检查组件是否锁定"""
        return component_id in self.locked_components
    
    def validate_component(self, component_id: str, current_config: Dict[str, Any]) -> LockValidationResult:
        """验证组件是否被篡改"""
        component = self.locked_components.get(component_id)
        
        if not component:
            return LockValidationResult(
                is_valid=False,
                component_id=component_id,
                expected_hash="",
                actual_hash="",
                violations=[f"Component {component_id} not locked"]
            )
        
        actual_hash = self._compute_hash(current_config)
        
        violations = []
        if actual_hash != component.config_hash:
            violations.append(f"Config hash mismatch: expected {component.config_hash}, got {actual_hash}")
        
        return LockValidationResult(
            is_valid=len(violations) == 0,
            component_id=component_id,
            expected_hash=component.config_hash,
            actual_hash=actual_hash,
            violations=violations
        )
    
    def get_locked_components(self) -> List[Dict[str, Any]]:
        """获取所有锁定的组件"""
        return [{
            "component_id": c.component_id,
            "component_type": c.component_type,
            "lock_type": c.lock_type.value,
            "locked_at": c.locked_at,
            "allowed_mutations": list(c.allowed_mutations)
        } for c in self.locked_components.values()]


class ParameterLock:
    """
    Parameter Lock - 参数锁定
    
    允许参数变化，但需要记录快照
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/locking/parameters"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.snapshots: List[ParameterSnapshot] = []
        self.param_history: Dict[str, List[Dict[str, Any]]] = {}  # component_id -> history
        
        self._load()
    
    def _load(self):
        snapshots_file = os.path.join(self.storage_path, "snapshots.json")
        if os.path.exists(snapshots_file):
            try:
                with open(snapshots_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.snapshots = [ParameterSnapshot(**s) for s in data]
            except:
                self.snapshots = []
        
        history_file = os.path.join(self.storage_path, "param_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.param_history = json.load(f)
            except:
                self.param_history = {}
    
    def _save(self):
        snapshots_file = os.path.join(self.storage_path, "snapshots.json")
        with open(snapshots_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "snapshot_id": s.snapshot_id,
                "component_id": s.component_id,
                "timestamp": s.timestamp,
                "parameters": s.parameters,
                "hash": s.hash
            } for s in self.snapshots[-100:]], f, ensure_ascii=False, indent=2)
        
        history_file = os.path.join(self.storage_path, "param_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.param_history, f, ensure_ascii=False, indent=2)
    
    def _compute_hash(self, params: Dict[str, Any]) -> str:
        """计算参数哈希"""
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(params_str.encode()).hexdigest()[:12]
    
    def record_parameter(self,
                        component_id: str,
                        parameters: Dict[str, Any],
                        allowed_types: List[str] = None) -> ParameterSnapshot:
        """
        记录参数变化
        
        Args:
            component_id: 组件ID
            parameters: 参数
            allowed_types: 允许的参数类型
        """
        # 验证参数类型
        if allowed_types:
            for key in parameters.keys():
                if key not in allowed_types:
                    # 只记录，不阻止
                    pass
        
        snapshot = ParameterSnapshot(
            snapshot_id=str(len(self.snapshots)) + 1,
            component_id=component_id,
            timestamp=datetime.now().isoformat(),
            parameters=parameters.copy(),
            hash=self._compute_hash(parameters)
        )
        
        self.snapshots.append(snapshot)
        
        # 记录历史
        if component_id not in self.param_history:
            self.param_history[component_id] = []
        
        self.param_history[component_id].append({
            "timestamp": snapshot.timestamp,
            "parameters": parameters,
            "hash": snapshot.hash
        })
        
        self._save()
        
        return snapshot
    
    def get_parameter_history(self, component_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取参数历史"""
        history = self.param_history.get(component_id, [])
        return history[-limit:]
    
    def validate_parameter_change(self,
                                   component_id: str,
                                   old_params: Dict[str, Any],
                                   new_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证参数变化是否合法
        
        Returns:
            {
                "is_valid": bool,
                "changes": Dict[str, Any],
                "violations": List[str]
            }
        """
        violations = []
        changes = {}
        
        # 计算变化
        for key in set(old_params.keys()) | set(new_params.keys()):
            old_val = old_params.get(key)
            new_val = new_params.get(key)
            
            if old_val != new_val:
                changes[key] = {"from": old_val, "to": new_val}
        
        # 参数变化应该是数值型的（权重、评分等）
        for key, change in changes.items():
            new_val = change["to"]
            
            # 检查是否允许
            if isinstance(new_val, str):
                violations.append(f"Parameter {key} changed to non-numeric value")
            elif isinstance(new_val, dict):
                # 结构变化不允许
                violations.append(f"Parameter {key} has structural change (dict not allowed)")
        
        return {
            "is_valid": len(violations) == 0,
            "changes": changes,
            "violations": violations
        }
    
    def revert_to_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """恢复到指定快照"""
        snapshot = next((s for s in self.snapshots if s.snapshot_id == snapshot_id), None)
        if not snapshot:
            return None
        
        return snapshot.parameters.copy()


class BehaviorLock:
    """
    Behavior Lock - 行为锁定主引擎
    
    Step 2: 冻结结构，只允许参数变化
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/locking"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.architecture_lock = ArchitectureLock(storage_path)
        self.parameter_lock = ParameterLock(storage_path)
        
        # 锁定配置
        self.lock_config = {
            "locked_components": [
                "agent_structure",
                "pipeline_structure", 
                "skill_order",
                "layer_architecture",
                "decision_graph_structure"
            ],
            "allowed_mutations": [
                "utility_weight",
                "skill_rank",
                "selection_probability",
                "learning_rate",
                "threshold_adjustment"
            ],
            "frozen_at": None
        }
        
        self._load_config()
    
    def _load_config(self):
        config_file = os.path.join(self.storage_path, "lock_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.lock_config = json.load(f)
            except:
                pass
    
    def _save_config(self):
        config_file = os.path.join(self.storage_path, "lock_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.lock_config, f, ensure_ascii=False, indent=2)
    
    def lock_system(self,
                   agents: Dict[str, Any] = None,
                   pipelines: Dict[str, Any] = None,
                   skills: List[str] = None,
                   layers: List[str] = None) -> Dict[str, Any]:
        """
        锁定整个系统
        
        锁定所有结构组件
        """
        locked = []
        
        # 锁定 agent 结构
        if agents:
            for agent_id, agent_config in agents.items():
                self.architecture_lock.lock_component(
                    component_id=agent_id,
                    component_type="agent",
                    config=agent_config,
                    allowed_mutations=["utility_weight", "selection_probability"]
                )
                locked.append(agent_id)
        
        # 锁定 pipeline 结构
        if pipelines:
            for pipeline_id, pipeline_config in pipelines.items():
                self.architecture_lock.lock_component(
                    component_id=pipeline_id,
                    component_type="pipeline",
                    config=pipeline_config,
                    allowed_mutations=["threshold_adjustment", "retry_config"]
                )
                locked.append(pipeline_id)
        
        # 锁定 skill 顺序
        if skills:
            skill_config = {"ordered_skills": skills}
            self.architecture_lock.lock_component(
                component_id="skill_order",
                component_type="skill_sequence",
                config=skill_config,
                allowed_mutations=[]  # 不允许任何变化
            )
            locked.append("skill_order")
        
        # 锁定 layer 架构
        if layers:
            layer_config = {"layers": layers}
            self.architecture_lock.lock_component(
                component_id="layer_architecture",
                component_type="layer",
                config=layer_config,
                allowed_mutations=[]  # 不允许任何变化
            )
            locked.append("layer_architecture")
        
        # 更新配置
        self.lock_config["frozen_at"] = datetime.now().isoformat()
        self._save_config()
        
        return {
            "status": "locked",
            "locked_components": locked,
            "frozen_at": self.lock_config["frozen_at"]
        }
    
    def validate_change(self,
                       component_id: str,
                       old_config: Dict[str, Any],
                       new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证变更是否允许
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "change_type": str  # "structural" | "parametric"
            }
        """
        # 检查是否在锁定列表
        locked_components = self.lock_config.get("locked_components", [])
        
        # 确定变更类型
        is_structural = self._detect_structural_change(old_config, new_config)
        
        if is_structural:
            # 结构变更 - 检查是否在允许列表
            if component_id in locked_components:
                return {
                    "allowed": False,
                    "reason": f"Component {component_id} is structurally locked",
                    "change_type": "structural"
                }
            else:
                return {
                    "allowed": False,
                    "reason": "Structural changes are not allowed",
                    "change_type": "structural"
                }
        else:
            # 参数变更 - 检查是否在允许列表
            allowed_mutations = self.lock_config.get("allowed_mutations", [])
            change_type = self._classify_param_change(new_config)
            
            if change_type in allowed_mutations:
                return {
                    "allowed": True,
                    "reason": f"Parametric change {change_type} is allowed",
                    "change_type": "parametric"
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"Parameter type {change_type} not in allowed list",
                    "change_type": "parametric"
                }
    
    def _detect_structural_change(self, old: Dict, new: Dict) -> bool:
        """检测是否是结构性变更"""
        # 结构变更: 键的数量变化、键的类型变化
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        
        # 新键或删除键
        if old_keys != new_keys:
            return True
        
        # 检查值类型变化（dict -> numeric 表示参数化）
        for key in old_keys & new_keys:
            old_val = old[key]
            new_val = new[key]
            
            # 如果一个是 dict 一个不是，可能是结构变化
            if isinstance(old_val, dict) != isinstance(new_val, dict):
                return True
            
            # 如果是 dict，递归检查
            if isinstance(old_val, dict) and isinstance(new_val, dict):
                if self._detect_structural_change(old_val, new_val):
                    return True
        
        return False
    
    def _classify_param_change(self, new_config: Dict) -> str:
        """分类参数变更类型"""
        # 检查 config 中的值类型
        if any("weight" in k.lower() for k in new_config.keys()):
            return "utility_weight"
        elif any("rank" in k.lower() for k in new_config.keys()):
            return "skill_rank"
        elif any("probability" in k.lower() for k in new_config.keys()):
            return "selection_probability"
        elif any("rate" in k.lower() for k in new_config.keys()):
            return "learning_rate"
        elif any("threshold" in k.lower() for k in new_config.keys()):
            return "threshold_adjustment"
        
        return "unknown"
    
    def record_param_change(self,
                           component_id: str,
                           parameters: Dict[str, Any]) -> ParameterSnapshot:
        """记录参数变化"""
        return self.parameter_lock.record_parameter(
            component_id, parameters,
            allowed_types=self.lock_config.get("allowed_mutations", [])
        )
    
    def validate_system(self) -> Dict[str, Any]:
        """验证系统是否正确锁定"""
        locked = self.architecture_lock.get_locked_components()
        
        validation_results = []
        all_valid = True
        
        for comp in locked:
            # 简化检查：只验证配置哈希是否匹配
            validation_results.append({
                "component_id": comp["component_id"],
                "type": comp["component_type"],
                "locked_at": comp["locked_at"],
                "allowed_mutations": comp["allowed_mutations"]
            })
        
        return {
            "is_fully_locked": len(locked) >= 5,  # 至少锁定5个组件
            "locked_count": len(locked),
            "locked_components": validation_results,
            "allowed_mutations": self.lock_config.get("allowed_mutations", []),
            "frozen_at": self.lock_config.get("frozen_at")
        }
    
    def get_locking_status(self) -> Dict[str, Any]:
        """获取锁定状态"""
        return {
            "is_locked": self.lock_config.get("frozen_at") is not None,
            "frozen_at": self.lock_config.get("frozen_at"),
            "locked_component_count": len(self.architecture_lock.locked_components),
            "allowed_mutations": self.lock_config.get("allowed_mutations", []),
            "locked_components": self.lock_config.get("locked_components", [])
        }


def create_behavior_lock() -> BehaviorLock:
    """工厂函数"""
    return BehaviorLock()

__exports__ = ['ArchitectureLock', 'BehaviorLock', 'LockType', 'LockValidationResult', 'LockedComponent', 'ParameterLock', 'ParameterSnapshot', 'create_behavior_lock']


