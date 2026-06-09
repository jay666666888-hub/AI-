#!/usr/bin/env python3
"""
World State Graph - 世界状态图
追踪实体关系、状态变化、因果链
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid


class EntityType(Enum):
    FILE = "file"
    MODULE = "module"
    SKILL = "skill"
    AGENT = "agent"
    LAYER = "layer"
    TASK = "task"


class EdgeType(Enum):
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    CONTAINS = "contains"


@dataclass
class Entity:
    id: str
    type: EntityType
    name: str
    properties: Dict[str, Any]
    state: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    relation: EdgeType
    weight: float


@dataclass
class StateChange:
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    timestamp: str
    cause: str


class WorldStateGraph:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/world_state"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.entities: Dict[str, Entity] = {}
        self.edges: List[Edge] = []
        self.state_changes: List[StateChange] = []
        self._load_graph()

    def _load_graph(self):
        entities_file = os.path.join(self.storage_path, "entities.json")
        if os.path.exists(entities_file):
            try:
                with open(entities_file, 'r', encoding='utf-8') as f:
                    self.entities = {k: Entity(**v) for k, v in json.load(f).items()}
            except:
                self.entities = {}

        edges_file = os.path.join(self.storage_path, "edges.json")
        if os.path.exists(edges_file):
            try:
                with open(edges_file, 'r', encoding='utf-8') as f:
                    self.edges = [Edge(**e) for e in json.load(f)]
            except:
                self.edges = []

        changes_file = os.path.join(self.storage_path, "state_changes.json")
        if os.path.exists(changes_file):
            try:
                with open(changes_file, 'r', encoding='utf-8') as f:
                    self.state_changes = [StateChange(**c) for c in json.load(f)]
            except:
                self.state_changes = []

    def _save_graph(self):
        with open(os.path.join(self.storage_path, "entities.json"), 'w') as f:
            json.dump({k: {"id": v.id, "type": v.type.value, "name": v.name,
                           "properties": v.properties, "state": v.state,
                           "created_at": v.created_at, "updated_at": v.updated_at}
                      for k, v in self.entities.items()}, f, ensure_ascii=False, indent=2)
        with open(os.path.join(self.storage_path, "edges.json"), 'w') as f:
            json.dump([{"id": e.id, "source_id": e.source_id, "target_id": e.target_id,
                       "relation": e.relation.value, "weight": e.weight} for e in self.edges], f)
        with open(os.path.join(self.storage_path, "state_changes.json"), 'w') as f:
            json.dump([{"entity_id": c.entity_id, "field": c.field, "old_value": c.old_value,
                       "new_value": c.new_value, "timestamp": c.timestamp, "cause": c.cause}
                      for c in self.state_changes], f, ensure_ascii=False, indent=2)

    def add_entity(self, entity_type: EntityType, name: str,
                   properties: Dict[str, Any] = None, state: Dict[str, Any] = None) -> str:
        entity_id = str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()
        self.entities[entity_id] = Entity(
            id=entity_id, type=entity_type, name=name,
            properties=properties or {}, state=state or {},
            created_at=now, updated_at=now
        )
        self._save_graph()
        return entity_id

    def update_entity_state(self, entity_id: str, field: str, value: Any, cause: str = "") -> bool:
        if entity_id not in self.entities:
            return False
        entity = self.entities[entity_id]
        old_value = entity.state.get(field)
        entity.state[field] = value
        entity.updated_at = datetime.now().isoformat()
        self.state_changes.append(StateChange(
            entity_id=entity_id, field=field, old_value=old_value,
            new_value=value, timestamp=datetime.now().isoformat(), cause=cause
        ))
        self._save_graph()
        return True

    def add_edge(self, source_id: str, target_id: str, relation: EdgeType, weight: float = 1.0) -> Optional[str]:
        if source_id not in self.entities or target_id not in self.entities:
            return None
        edge_id = str(uuid.uuid4())[:8]
        self.edges.append(Edge(id=edge_id, source_id=source_id, target_id=target_id, relation=relation, weight=weight))
        self._save_graph()
        return edge_id

    def get_neighbors(self, entity_id: str) -> List[Entity]:
        neighbor_ids = set()
        for edge in self.edges:
            if edge.source_id == entity_id:
                neighbor_ids.add(edge.target_id)
            elif edge.target_id == entity_id:
                neighbor_ids.add(edge.source_id)
        return [self.entities[nid] for nid in neighbor_ids if nid in self.entities]

    def get_graph_summary(self) -> Dict[str, Any]:
        by_type = {}
        for entity in self.entities.values():
            type_name = entity.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        return {
            "total_entities": len(self.entities),
            "total_edges": len(self.edges),
            "entities_by_type": by_type
        }


def create_world_state_graph() -> WorldStateGraph:
    return WorldStateGraph()
__exports__ = ['Edge', 'EdgeType', 'Entity', 'EntityType', 'StateChange', 'WorldStateGraph', 'create_world_state_graph']


