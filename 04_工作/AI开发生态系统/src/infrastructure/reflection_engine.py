#!/usr/bin/env python3
"""
Reflection Engine - 反思引擎
执行后分析、模式识别、改进建议
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ReflectionLevel(Enum):
    SURFACE = "surface"
    PATTERN = "pattern"
    CAUSAL = "causal"
    METACOGNITIVE = "metacognitive"


@dataclass
class Reflection:
    id: str
    timestamp: str
    level: ReflectionLevel
    trigger: str
    observations: List[str]
    patterns: List[str]
    root_causes: List[str]
    improvements: List[str]
    confidence: float


@dataclass
class Pattern:
    name: str
    frequency: int
    severity: str
    examples: List[str]
    mitigation: str


class ReflectionEngine:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/reflection"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.reflections: List[Reflection] = []
        self.patterns: Dict[str, Pattern] = {}
        self._load_reflections()

    def _load_reflections(self):
        history_file = os.path.join(self.storage_path, "reflections.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reflections = [Reflection(**r) for r in data]
            except:
                self.reflections = []

        patterns_file = os.path.join(self.storage_path, "patterns.json")
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = {k: Pattern(**v) for k, v in data.items()}
            except:
                self.patterns = {}

    def _save_reflections(self):
        history_file = os.path.join(self.storage_path, "reflections.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "id": r.id, "timestamp": r.timestamp, "level": r.level.value,
                "trigger": r.trigger, "observations": r.observations,
                "patterns": r.patterns, "root_causes": r.root_causes,
                "improvements": r.improvements, "confidence": r.confidence
            } for r in self.reflections], f, ensure_ascii=False, indent=2)

    def _save_patterns(self):
        patterns_file = os.path.join(self.storage_path, "patterns.json")
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump({k: {
                "name": v.name, "frequency": v.frequency, "severity": v.severity,
                "examples": v.examples, "mitigation": v.mitigation
            } for k, v in self.patterns.items()}, f, ensure_ascii=False, indent=2)

    def reflect(self, trigger: str, observations: List[str],
                level: ReflectionLevel = ReflectionLevel.SURFACE) -> Reflection:
        reflection_id = f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        patterns = self._identify_patterns(observations)
        root_causes = self._analyze_root_causes(observations, patterns) if level.value >= "causal" else []
        improvements = self._generate_improvements(patterns, root_causes) if level.value.value >= "metacognitive" else []

        reflection = Reflection(
            id=reflection_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            trigger=trigger,
            observations=observations,
            patterns=patterns,
            root_causes=root_causes,
            improvements=improvements,
            confidence=0.7 + len(observations) * 0.05
        )

        self.reflections.append(reflection)
        self._update_patterns(patterns)
        self._save_reflections()
        self._save_patterns()

        return reflection

    def _identify_patterns(self, observations: List[str]) -> List[str]:
        patterns_found = []
        obs_text = " ".join(observations).lower()

        pattern_rules = {
            "repeated_failure": ["失败", "error", "failed"],
            "timeout_issue": ["超时", "timeout", "等待"],
            "import_error": ["import", "导入", "module not found"],
            "permission_denied": ["权限", "permission", "denied"],
            "resource_exhausted": ["内存", "memory", "资源"],
            "network_issue": ["网络", "network", "连接"],
        }

        for pattern_name, keywords in pattern_rules.items():
            if sum(1 for kw in keywords if kw.lower() in obs_text) >= 2:
                patterns_found.append(pattern_name)

        return patterns_found

    def _analyze_root_causes(self, observations: List[str], patterns: List[str]) -> List[str]:
        causes = []
        cause_map = {
            "repeated_failure": "可能是流程设计问题或环境不稳定",
            "timeout_issue": "可能是资源不足或外部依赖响应慢",
            "import_error": "可能是依赖管理或路径配置问题",
            "permission_denied": "可能是容器权限配置问题",
            "resource_exhausted": "可能是内存泄漏或资源限制过小",
            "network_issue": "可能是网络策略或防火墙问题",
        }
        for pattern in patterns:
            causes.append(cause_map.get(pattern, f"未知原因: {pattern}"))
        return causes

    def _generate_improvements(self, patterns: List[str], root_causes: List[str]) -> List[str]:
        improvements = []
        improvement_map = {
            "repeated_failure": "添加重试机制 + 熔断器",
            "timeout_issue": "增加 timeout 配置",
            "import_error": "检查依赖管理和模块路径",
            "permission_denied": "检查 Docker/容器权限配置",
            "resource_exhausted": "增加资源限制或优化内存使用",
            "network_issue": "添加网络重试和降级策略",
        }
        for pattern in patterns:
            improvements.append(improvement_map.get(pattern, f"需要分析: {pattern}"))
        return improvements

    def _update_patterns(self, patterns: List[str]):
        for pattern_name in patterns:
            if pattern_name in self.patterns:
                self.patterns[pattern_name].frequency += 1
            else:
                self.patterns[pattern_name] = Pattern(
                    name=pattern_name, frequency=1, severity="medium", examples=[], mitigation=""
                )

    def get_recent_reflections(self, limit: int = 10) -> List[Dict[str, Any]]:
        return sorted([{
            "id": r.id, "timestamp": r.timestamp, "level": r.level.value,
            "trigger": r.trigger, "patterns": r.patterns, "improvements": r.improvements
        } for r in self.reflections], key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_improvement_suggestions(self) -> List[str]:
        suggestions = []
        for reflection in sorted(self.reflections, key=lambda x: x.timestamp, reverse=True)[:5]:
            suggestions.extend(reflection.improvements)
        return list(set(suggestions))
__exports__ = ['Pattern', 'Reflection', 'ReflectionEngine', 'ReflectionLevel']


