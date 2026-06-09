#!/usr/bin/env python3
"""
Timeline Store - Causal Ordered Event Log
时序事实存储：只存"演化过程"，不存"结果"
"""

import sys
import os
import json
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


@dataclass
class TimelineEntry:
    """时间线条目"""
    date: str  # YYYY-MM-DD
    event_file: str  # 文件名
    event_count: int
    first_event: str  # timestamp
    last_event: str


class TimelineStore:
    """
    Timeline Store - causal ordered event log
    
    结构：
    timeline/
      2026-05-15/
        exec_001.json
        exec_002.json
      2026-05-16/
        exec_001.json
    
    关键点：
    ❗️ 不存"结果"，只存"演化过程"
    ✅ append-only
    ✅ ordered by timestamp
    ✅ immutable
    """

    def __init__(self, base_path: str = None):
        self.base_path = base_path or "/tmp/telemetry/timeline"
        self._ensure_directory()

    def _ensure_directory(self):
        """确保目录存在"""
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def _get_date_dir(self, timestamp: str = None) -> str:
        """获取日期目录路径"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        date_str = timestamp[:10]  # YYYY-MM-DD
        return os.path.join(self.base_path, date_str)

    def _get_date_index_file(self, date_dir: str) -> str:
        """获取日期索引文件"""
        return os.path.join(date_dir, "_index.json")

    def append(self, event_data: Dict[str, Any], event_id: str = None) -> str:
        """
        追加事件到时间线
        返回事件文件名
        """
        if event_id is None:
            event_id = event_data.get('action_id', datetime.now().strftime('%H%M%S_%f'))

        # 获取日期目录
        timestamp = event_data.get('timestamp', datetime.now().isoformat())
        date_dir = self._get_date_dir(timestamp)
        Path(date_dir).mkdir(exist_ok=True)

        # 生成文件名
        date_events = self._get_date_events(date_dir)
        filename = f"exec_{len(date_events) + 1:06d}.json"
        filepath = os.path.join(date_dir, filename)

        # 写入事件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)

        # 更新索引
        self._update_index(date_dir, filename, event_data)

        return filepath

    def _get_date_events(self, date_dir: str) -> List[str]:
        """获取某天的所有事件文件"""
        if not os.path.exists(date_dir):
            return []
        return [f for f in os.listdir(date_dir) if f.startswith('exec_') and f.endswith('.json')]

    def _update_index(self, date_dir: str, filename: str, event_data: Dict):
        """更新日期索引"""
        index_file = self._get_date_index_file(date_dir)

        index = {}
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)

        index[filename] = {
            "action_id": event_data.get('action_id'),
            "timestamp": event_data.get('timestamp'),
            "event_type": event_data.get('event_type'),
            "agent_id": event_data.get('agent_id'),
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def get_events_by_date(self, date: str) -> List[Dict]:
        """获取某天的所有事件"""
        date_dir = os.path.join(self.base_path, date)
        if not os.path.exists(date_dir):
            return []

        events = []
        for filename in sorted(os.listdir(date_dir)):
            if not filename.startswith('exec_') or not filename.endswith('.json'):
                continue
            filepath = os.path.join(date_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                events.append(json.load(f))

        return events

    def get_events_in_range(self, start: str, end: str) -> List[Dict]:
        """获取时间范围内的事件"""
        all_events = []

        start_date = datetime.fromisoformat(start[:10])
        end_date = datetime.fromisoformat(end[:10])

        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            events = self.get_events_by_date(date_str)

            for event in events:
                if start <= event.get('timestamp', '') <= end:
                    all_events.append(event)

            current += timedelta(days=1)

        return sorted(all_events, key=lambda x: x.get('timestamp', ''))

    def get_event(self, date: str, filename: str) -> Optional[Dict]:
        """获取单个事件"""
        filepath = os.path.join(self.base_path, date, filename)
        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_timeline_entries(self) -> List[TimelineEntry]:
        """获取所有时间线条目"""
        entries = []

        if not os.path.exists(self.base_path):
            return entries

        for date_dir in sorted(os.listdir(self.base_path)):
            full_path = os.path.join(self.base_path, date_dir)
            if not os.path.isdir(full_path):
                continue

            events = self.get_events_by_date(date_dir)
            if not events:
                continue

            entries.append(TimelineEntry(
                date=date_dir,
                event_file=f"{len(events)} events",
                event_count=len(events),
                first_event=events[0].get('timestamp', ''),
                last_event=events[-1].get('timestamp', '')
            ))

        return entries

    def export_day(self, date: str, output_path: str = None) -> str:
        """导出一整天的事件"""
        events = self.get_events_by_date(date)

        if output_path is None:
            output_path = f"/tmp/telemetry_export_{date}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

        return output_path

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        total_events = 0
        total_days = 0

        if os.path.exists(self.base_path):
            for date_dir in os.listdir(self.base_path):
                full_path = os.path.join(self.base_path, date_dir)
                if os.path.isdir(full_path):
                    events = self.get_events_by_date(date_dir)
                    total_events += len(events)
                    if events:
                        total_days += 1

        return {
            "total_events": total_events,
            "total_days": total_days,
            "storage_path": self.base_path,
        }


# Global instance
_store: Optional[TimelineStore] = None


def get_timeline_store() -> TimelineStore:
    global _store
    if _store is None:
        _store = TimelineStore()
    return _store


if __name__ == "__main__":
    print("=" * 60)
    print("Timeline Store - Causal Ordered Event Log")
    print("=" * 60)

    store = get_timeline_store()

    # 测试添加事件
    print("\n[1] Appending test events...")

    from execution_logger import ExecutionEvent, EventType, get_logger

    logger = get_logger()

    # 创建测试事件
    event = ExecutionEvent(
        action_id="test_001",
        timestamp=datetime.now().isoformat(),
        event_type=EventType.ROUTING.value,
        agent_id="planner",
        task_type="build",
        selected_option="planner"
    )

    filepath = store.append(event.to_dict())
    print(f"    Appended to: {filepath}")

    # 再添加几个
    for i in range(5):
        event = ExecutionEvent(
            action_id=f"test_{i:03d}",
            timestamp=datetime.now().isoformat(),
            event_type=EventType.UTILITY_EVAL.value,
            utility_input={"cost": 0.5, "speed": 0.7},
            utility_output=0.65
        )
        store.append(event.to_dict())

    # 统计
    print("\n[2] Store statistics:")
    stats = store.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # 时间线条目
    print("\n[3] Timeline entries:")
    for entry in store.get_timeline_entries():
        print(f"    {entry.date}: {entry.event_count} events ({entry.first_event[:19]} - {entry.last_event[:19]})")

    print("\n" + "=" * 60)
    print("Timeline Store ready - append-only causal log")
    print("=" * 60)
