#!/usr/bin/env python3
"""
Evolution Skill - 自我进化引擎
从历史执行中学习，自动优化路由和工作流
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


EVOLUTION_DIR = os.path.expanduser("~/.claude/projects/-mnt-c-Users-Admin/evolution")

_evolution_skill = None


@dataclass
class ExecutionRecord:
    task: str
    task_type: str
    skills: List[str]
    agents: List[str]
    success: bool
    duration_ms: int
    feedback: str
    timestamp: str
    layers_used: List[str]


class EvolutionTracker:
    def __init__(self):
        self.evolution_dir = EVOLUTION_DIR
        os.makedirs(self.evolution_dir, exist_ok=True)
        self.history_file = os.path.join(self.evolution_dir, 'execution_history.json')
        self.rates_file = os.path.join(self.evolution_dir, 'task_success_rates.json')
        self.performance_file = os.path.join(self.evolution_dir, 'skill_performance.json')
        self.records: List[ExecutionRecord] = []
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [ExecutionRecord(**r) for r in data]
            except:
                self.records = []

    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.records], f, ensure_ascii=False, indent=2)

    def record(self, task, task_type, skills, agents, success, duration_ms, feedback='', layers_used=None):
        record = ExecutionRecord(
            task=task, task_type=task_type, skills=skills, agents=agents,
            success=success, duration_ms=duration_ms, feedback=feedback,
            timestamp=datetime.now().isoformat(), layers_used=layers_used or []
        )
        self.records.append(record)
        self._save_history()
        self._update_rates()
        self._update_performance()
        return {'status': 'recorded', 'total_records': len(self.records)}

    def _update_rates(self):
        rates = defaultdict(lambda: {'total': 0, 'success': 0})
        for r in self.records:
            rates[r.task_type]['total'] += 1
            if r.success:
                rates[r.task_type]['success'] += 1
        result = {tt: {'total': d['total'], 'success': d['success'], 'rate': d['success']/d['total'] if d['total'] > 0 else 0} for tt, d in rates.items()}
        with open(self.rates_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def _update_performance(self):
        perf = defaultdict(lambda: {'total': 0, 'success': 0, 'total_duration': 0})
        for r in self.records:
            for skill in r.skills:
                perf[skill]['total'] += 1
                if r.success:
                    perf[skill]['success'] += 1
                perf[skill]['total_duration'] += r.duration_ms
        for name, data in perf.items():
            data['avg_duration'] = data['total_duration'] / data['total'] if data['total'] > 0 else 0
            data['success_rate'] = data['success'] / data['total'] if data['total'] > 0 else 0
        with open(self.performance_file, 'w', encoding='utf-8') as f:
            json.dump(dict(perf), f, ensure_ascii=False, indent=2)

    def get_skill_success_rate(self, skill):
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                return json.load(f).get(skill, {}).get('success_rate', 0.5)
        return 0.5

    def get_task_type_success_rate(self, task_type):
        if os.path.exists(self.rates_file):
            with open(self.rates_file, 'r', encoding='utf-8') as f:
                return json.load(f).get(task_type, {}).get('rate', 0.5)
        return 0.5

    def get_stats(self):
        if not self.records:
            return {'total': 0, 'evolution_enabled': True}
        success_count = sum(1 for r in self.records if r.success)
        return {'total': len(self.records), 'success': success_count, 'success_rate': success_count/len(self.records), 'evolution_enabled': True}


class AdaptiveRouter:
    def __init__(self, tracker=None):
        self.tracker = tracker or EvolutionTracker()

    def adjust_recommendation(self, base_skills, task_type):
        if not base_skills:
            return base_skills
        scored = [(s, self.tracker.get_skill_success_rate(s)) for s in base_skills]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored]


class EvolutionSkill:
    def __init__(self):
        self.tracker = EvolutionTracker()
        self.adaptive = AdaptiveRouter(self.tracker)

    def record_execution(self, task, task_type, skills, agents, success, duration_ms, feedback='', layers=None):
        return self.tracker.record(task, task_type, skills, agents, success, duration_ms, feedback, layers)

    def get_adaptive_skills(self, base_skills, task_type):
        return self.adaptive.adjust_recommendation(base_skills, task_type)

    def get_status(self):
        return {'evolution_enabled': True, 'records': len(self.tracker.records), 'stats': self.tracker.get_stats()}


def get_evolution_skill():
    global _evolution_skill
    if _evolution_skill is None:
        _evolution_skill = EvolutionSkill()
    return _evolution_skill
