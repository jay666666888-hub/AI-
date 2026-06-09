#!/usr/bin/env python3
"""
Transaction + Rollback System
事务与回滚系统 - 保证操作原子性
"""

import os
import json
import copy
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class TransactionStatus(Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class TransactionRecord:
    id: str
    operation: str
    timestamp: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    target_files: List[str]
    status: TransactionStatus
    error: str = ""


class RollbackRegistry:
    """回滚注册表"""

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/rollback"
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        self.transactions: List[TransactionRecord] = []
        self._load_transactions()

    def _load_transactions(self):
        history_file = os.path.join(self.storage_dir, "transactions.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.transactions = [TransactionRecord(**t) for t in data]
            except:
                self.transactions = []

    def _save_transactions(self):
        history_file = os.path.join(self.storage_dir, "transactions.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(t) for t in self.transactions], f, ensure_ascii=False, indent=2)

    def record_transaction(
        self,
        operation: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        target_files: List[str] = None
    ) -> str:
        tx_id = f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        record = TransactionRecord(
            id=tx_id,
            operation=operation,
            timestamp=datetime.now().isoformat(),
            before_state=before_state,
            after_state=after_state,
            target_files=target_files or [],
            status=TransactionStatus.PENDING
        )
        self.transactions.append(record)
        self._save_transactions()
        return tx_id

    def commit(self, tx_id: str) -> bool:
        for tx in self.transactions:
            if tx.id == tx_id:
                tx.status = TransactionStatus.COMMITTED
                self._save_transactions()
                return True
        return False

    def rollback(self, tx_id: str) -> Dict[str, Any]:
        for tx in self.transactions:
            if tx.id == tx_id:
                if tx.status == TransactionStatus.ROLLED_BACK:
                    return {"status": "already_rolled_back", "tx_id": tx_id}

                restored = {}
                for file_path in tx.target_files:
                    if os.path.exists(file_path):
                        backup_path = f"{file_path}.backup"
                        with open(file_path, 'r', encoding='utf-8') as f:
                            current = f.read()
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(current)

                        if tx.before_state.get(file_path):
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(tx.before_state[file_path])
                            restored[file_path] = "restored"

                tx.status = TransactionStatus.ROLLED_BACK
                self._save_transactions()

                return {"status": "rolled_back", "tx_id": tx_id, "restored": restored}
        return {"status": "not_found", "tx_id": tx_id}

    def get_recent(self, limit: int = 10) -> List[TransactionRecord]:
        return sorted(self.transactions, key=lambda x: x.timestamp, reverse=True)[:limit]


class FileSnapshot:
    """文件快照"""

    SNAPSHOT_DIR = os.path.expanduser("~/.claude/projects/-mnt-c-Users-Admin/snapshots")

    def __init__(self):
        self.snapshot_dir = self.SNAPSHOT_DIR
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def take_snapshot(self, file_path: str, metadata: str = "") -> str:
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        snapshot_id = f"{os.path.basename(file_path)}_{timestamp}"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        snapshot_data = {
            "id": snapshot_id,
            "original_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "content": content
        }

        snapshot_file = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        snapshot_file = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        if not os.path.exists(snapshot_file):
            return False

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        target_path = data["original_path"]
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(data["content"])

        return True

    def list_snapshots(self, file_path: str = None) -> List[Dict[str, Any]]:
        snapshots = []
        for fname in os.listdir(self.snapshot_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.snapshot_dir, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if file_path is None or data["original_path"] == file_path:
                        snapshots.append({
                            "id": data["id"],
                            "original_path": data["original_path"],
                            "timestamp": data["timestamp"],
                            "metadata": data.get("metadata", "")
                        })
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)


class TransactionContext:
    """事务上下文管理器"""

    def __init__(self, name: str, registry: RollbackRegistry = None):
        self.name = name
        self.registry = registry or RollbackRegistry()
        self.tx_id: Optional[str] = None
        self.before_states: Dict[str, str] = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.tx_id:
                self.registry.rollback(self.tx_id)
            return False
        return True

    def capture_files(self, file_paths: List[str]):
        for path in file_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.before_states[path] = f.read()

    def commit(self, operation: str, after_states: Dict[str, str] = None):
        all_states = {"before": self.before_states, "after": after_states or {}}
        self.tx_id = self.registry.record_transaction(
            operation=operation,
            before_state=self.before_states,
            after_state=after_states or {},
            target_files=list(self.before_states.keys())
        )
        self.registry.commit(self.tx_id)
        return self.tx_id


def create_transaction(operation: str) -> TransactionContext:
    return TransactionContext(operation)
__exports__ = ['FileSnapshot', 'RollbackRegistry', 'TransactionContext', 'TransactionRecord', 'TransactionStatus', 'create_transaction']


