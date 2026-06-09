#!/usr/bin/env python3
"""
Runtime State Recovery - 运行时状态恢复
断点保存 + 状态恢复 + Crash Recovery
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class CheckpointStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass
class Checkpoint:
    id: str
    stage: str
    timestamp: str
    state: Dict[str, Any]
    skills_state: Dict[str, Any]
    pipeline_position: int
    total_stages: int
    metadata: Dict[str, Any]


class StateManager:
    CHECKPOINT_DIR = os.path.expanduser("~/.claude/projects/-mnt-c-Users-Admin/checkpoints")

    def __init__(self):
        self.checkpoint_dir = self.CHECKPOINT_DIR
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.current_checkpoint: Optional[Checkpoint] = None

    def save_checkpoint(
        self,
        stage: str,
        pipeline_position: int,
        total_stages: int,
        state: Dict[str, Any],
        skills_state: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        checkpoint_id = f"ckpt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        checkpoint = Checkpoint(
            id=checkpoint_id,
            stage=stage,
            timestamp=datetime.now().isoformat(),
            state=state,
            skills_state=skills_state or {},
            pipeline_position=pipeline_position,
            total_stages=total_stages,
            metadata=metadata or {}
        )

        checkpoint_file = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.json")
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(checkpoint), f, ensure_ascii=False, indent=2)

        latest_link = os.path.join(self.checkpoint_dir, "latest.json")
        with open(latest_link, 'w', encoding='utf-8') as f:
            json.dump({"latest": checkpoint_id, "timestamp": datetime.now().isoformat()}, f)

        self.current_checkpoint = checkpoint
        return checkpoint_id

    def load_latest_checkpoint(self) -> Optional[Checkpoint]:
        latest_link = os.path.join(self.checkpoint_dir, "latest.json")
        if not os.path.exists(latest_link):
            return None

        try:
            with open(latest_link, 'r', encoding='utf-8') as f:
                data = json.load(f)
                checkpoint_id = data.get("latest")

            checkpoint_file = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.json")
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_checkpoint = Checkpoint(**data)
                    return self.current_checkpoint
        except:
            pass
        return None

    def get_recovery_point(self) -> Optional[Checkpoint]:
        if not os.path.exists(self.checkpoint_dir):
            return None

        checkpoints = []
        for fname in os.listdir(self.checkpoint_dir):
            if fname.endswith(".json") and fname != "latest.json":
                fpath = os.path.join(self.checkpoint_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        checkpoints.append(Checkpoint(**data))
                except:
                    pass

        if not checkpoints:
            return None

        for ckpt in sorted(checkpoints, key=lambda x: x.timestamp, reverse=True):
            if ckpt.metadata.get("status") != "completed":
                return ckpt

        return checkpoints[-1] if checkpoints else None

    def mark_completed(self, checkpoint_id: str) -> bool:
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.json")
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["metadata"]["status"] = "completed"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        return False

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        checkpoints = []
        for fname in os.listdir(self.checkpoint_dir):
            if fname.endswith(".json") and fname != "latest.json":
                fpath = os.path.join(self.checkpoint_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        checkpoints.append({
                            "id": data["id"],
                            "stage": data["stage"],
                            "timestamp": data["timestamp"],
                            "position": f"{data['pipeline_position']}/{data['total_stages']}",
                            "status": data.get("metadata", {}).get("status", "unknown")
                        })
                except:
                    pass
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)


class RecoveryManager:
    def __init__(self, state_manager: StateManager = None):
        self.state_manager = state_manager or StateManager()
        self.recovery_handlers: Dict[str, Callable] = {}

    def register_handler(self, stage: str, handler: Callable):
        self.recovery_handlers[stage] = handler

    def recover(self) -> Dict[str, Any]:
        checkpoint = self.state_manager.get_recovery_point()

        if not checkpoint:
            return {"status": "no_recovery_point", "message": "No checkpoint found"}

        results = {
            "status": "recovered",
            "checkpoint_id": checkpoint.id,
            "stage": checkpoint.stage,
            "position": checkpoint.pipeline_position,
            "state": checkpoint.state,
            "handlers_executed": []
        }

        handler = self.recovery_handlers.get(checkpoint.stage)
        if handler:
            try:
                handler_result = handler(checkpoint)
                results["handlers_executed"].append({"stage": checkpoint.stage, "result": handler_result})
            except Exception as e:
                results["handlers_executed"].append({"stage": checkpoint.stage, "error": str(e)})

        checkpoint.metadata["status"] = "recovered"
        checkpoint.metadata["recovered_at"] = datetime.now().isoformat()

        return results

    def resume_pipeline(self, from_checkpoint: str = None) -> Dict[str, Any]:
        if from_checkpoint:
            checkpoint_file = os.path.join(self.state_manager.checkpoint_dir, f"{from_checkpoint}.json")
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    checkpoint = Checkpoint(**data)
            else:
                return {"status": "not_found", "checkpoint_id": from_checkpoint}
        else:
            checkpoint = self.state_manager.get_recovery_point()
            if not checkpoint:
                return {"status": "no_recovery_point"}

        return {
            "status": "ready_to_resume",
            "checkpoint_id": checkpoint.id,
            "stage": checkpoint.stage,
            "pipeline_position": checkpoint.pipeline_position,
            "remaining_stages": checkpoint.total_stages - checkpoint.pipeline_position,
            "state": checkpoint.state
        }


def get_state_manager() -> StateManager:
    return StateManager()
__exports__ = ['Checkpoint', 'CheckpointStatus', 'RecoveryManager', 'StateManager', 'get_state_manager']


