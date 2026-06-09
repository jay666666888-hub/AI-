#!/usr/bin/env python3
"""
Partial Success Model - 部分成功处理
支持软状态、部分完成、补偿事务
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"


@dataclass
class StageResult:
    stage: str
    status: StageStatus
    output: Any
    error: str
    duration_ms: int
    compensatable: bool = False
    partial_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    overall_status: str
    completed_stages: int
    total_stages: int
    success_rate: float
    stage_results: List[StageResult]
    partial_outputs: Dict[str, Any]
    requires_retry: bool
    requires_rollback: bool
    can_continue: bool


class PartialSuccessHandler:
    def __init__(self):
        self.stage_results: List[StageResult] = []
        self.compensation_handlers: Dict[str, Callable] = {}

    def register_compensation(self, stage: str, handler: Callable):
        self.compensation_handlers[stage] = handler

    def record_stage(self, result: StageResult):
        self.stage_results.append(result)

    def get_partial_outputs(self) -> Dict[str, Any]:
        partial = {}
        for result in self.stage_results:
            if result.status == StageStatus.PARTIAL and result.partial_data:
                partial[result.stage] = result.partial_data
            elif result.status == StageStatus.SUCCESS and result.output:
                partial[result.stage] = result.output
        return partial

    def should_rollback(self) -> bool:
        failed_stages = [r for r in self.stage_results if r.status == StageStatus.FAILED]
        return any(not r.compensatable for r in failed_stages)

    def should_retry(self) -> bool:
        return any(r.status == StageStatus.FAILED for r in self.stage_results)

    def can_continue(self) -> bool:
        critical_failed = [
            r for r in self.stage_results
            if r.status == StageStatus.FAILED and not r.compensatable
        ]
        return len(critical_failed) == 0

    def execute_compensations(self) -> Dict[str, Any]:
        results = {}
        for result in self.stage_results:
            if result.status in (StageStatus.SUCCESS, StageStatus.PARTIAL):
                if result.compensatable and result.stage in self.compensation_handlers:
                    try:
                        compensation_result = self.compensation_handlers[result.stage]()
                        result.status = StageStatus.COMPENSATED
                        results[result.stage] = {"status": "compensated", "result": compensation_result}
                    except Exception as e:
                        results[result.stage] = {"status": "failed", "error": str(e)}
        return results

    def build_pipeline_result(self, total_stages: int) -> PipelineResult:
        completed = sum(1 for r in self.stage_results if r.status == StageStatus.SUCCESS)
        partial = sum(1 for r in self.stage_results if r.status == StageStatus.PARTIAL)
        failed = sum(1 for r in self.stage_results if r.status == StageStatus.FAILED)

        overall_status = "success"
        if failed > 0 and not self.can_continue():
            overall_status = "failed"
        elif partial > 0 or (failed > 0 and self.can_continue()):
            overall_status = "partial"

        return PipelineResult(
            overall_status=overall_status,
            completed_stages=len([r for r in self.stage_results if r.status == StageStatus.SUCCESS]),
            total_stages=total_stages,
            success_rate=(completed + partial * 0.5) / total_stages if total_stages > 0 else 0,
            stage_results=self.stage_results,
            partial_outputs=self.get_partial_outputs(),
            requires_retry=self.should_retry(),
            requires_rollback=self.should_rollback(),
            can_continue=self.can_continue()
        )
__exports__ = ['PartialSuccessHandler', 'PipelineResult', 'StageResult', 'StageStatus']


