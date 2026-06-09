#!/bin/bash
# Delayed Outcome Tracker 处理脚本
# 每5分钟执行一次，处理到期的延迟检查点

cd /mnt/e/黑曜石/04_工作/AI开发生态系统
source venv/bin/activate 2>/dev/null || true
python -c "
import sys
sys.path.insert(0, 'src')
from infrastructure.tools.delayed_outcome_tracker import DelayedOutcomeTracker

tracker = DelayedOutcomeTracker()
results = tracker.process_due_checks()

if results:
    print(f'Processed {len(results)} delayed checks')
    for r in results:
        print(f'  {r[\"task_id\"]}: {r[\"checkpoint\"]} → {r[\"outcome\"]}')
" 2>&1 | tee -a /mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/delayed/process_delayed.log
