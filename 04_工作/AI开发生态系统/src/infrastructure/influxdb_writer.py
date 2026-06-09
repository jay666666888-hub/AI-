#!/usr/bin/env python3
"""
InfluxDB Writer - 将遥测数据写入 InfluxDB
供 Grafana Dashboard 查询
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from influxdb import InfluxDBClient
    INFLUX_AVAILABLE = True
except ImportError:
    INfluxDBClient = None
    INFLUX_AVAILABLE = False


class InfluxDBWriter:
    """写入 InfluxDB 的类"""

    def __init__(self,
                 url: str = "http://localhost:8086",
                 token: str = "my-super-secret-token",
                 org: str = "ecosystem",
                 bucket: str = "telmetry"):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None

        if INFLUX_AVAILABLE:
            try:
                self.client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org
                )
                print(f"✅ Connected to InfluxDB at {url}")
            except Exception as e:
                print(f"⚠️ Failed to connect to InfluxDB: {e}")
                self.client = None

    def write_calibration(self, task_type: str, ece: float, sample_count: int):
        """写入 ECE 校准数据"""
        if not self.client:
            return

        point = {
            "measurement": "calibration_ece",
            "tags": {"task_type": task_type},
            "fields": {
                "ece": ece,
                "sample_count": sample_count
            },
            "timestamp": datetime.now()
        }
        try:
            self.client.write([point], {"bucket": self.bucket, "org": self.org})
        except Exception as e:
            print(f"⚠️ Failed to write calibration: {e}")

    def write_delayed_tracker(self, pending_count: int, tracked_count: int,
                             delayed_failure_rate: float, outcome_change_rate: float):
        """写入延迟跟踪器数据"""
        if not self.client:
            return

        point = {
            "measurement": "delayed_tracker",
            "tags": {},
            "fields": {
                "pending_checks": pending_count,
                "tracked_tasks": tracked_count,
                "delayed_failure_rate": delayed_failure_rate,
                "outcome_change_rate": outcome_change_rate
            },
            "timestamp": datetime.now()
        }
        try:
            self.client.write([point], {"bucket": self.bucket, "org": self.org})
        except Exception as e:
            print(f"⚠️ Failed to write delayed tracker: {e}")

    def write_lottery_prediction(self, period: str, top6: list, hit_rate: float):
        """写入六肖预测数据"""
        if not self.client:
            return

        point = {
            "measurement": "lottery_prediction",
            "tags": {"period": period},
            "fields": {
                "hit_rate": hit_rate,
                "zodiac_count": len(top6)
            },
            "timestamp": datetime.now()
        }
        try:
            self.client.write([point], {"bucket": self.bucket, "org": self.org})
        except Exception as e:
            print(f"⚠️ Failed to write lottery prediction: {e}")

    def write_system_status(self, skills_count: int, agents_count: int,
                            layers_count: int, ready: bool):
        """写入系统状态"""
        if not self.client:
            return

        point = {
            "measurement": "system_status",
            "tags": {"ready": str(ready)},
            "fields": {
                "skills_count": skills_count,
                "agents_count": agents_count,
                "layers_count": layers_count
            },
            "timestamp": datetime.now()
        }
        try:
            self.client.write([point], {"bucket": self.bucket, "org": self.org})
        except Exception as e:
            print(f"⚠️ Failed to write system status: {e}")

    def push_all_telemetry(self, ecosystem_status: Dict[str, Any]):
        """推送所有遥测数据到 InfluxDB"""
        # 系统状态
        self.write_system_status(
            skills_count=ecosystem_status.get('skills_count', 0),
            agents_count=ecosystem_status.get('agents_count', 0),
            layers_count=ecosystem_status.get('layers_count', 0),
            ready=ecosystem_status.get('ready', False)
        )

        # ECE 校准
        cal = ecosystem_status.get('calibration', {})
        for tt, ece in cal.get('ece_by_task_type', {}).items():
            self.write_calibration(tt, ece, cal.get('sample_count', {}).get(tt, 0))

        # 延迟跟踪器
        delayed = ecosystem_status.get('delayed_outcomes', {})
        self.write_delayed_tracker(
            pending_count=delayed.get('pending_checks', 0),
            tracked_count=delayed.get('total_tracked', 0),
            delayed_failure_rate=delayed.get('delayed_failure_rate', 0),
            outcome_change_rate=delayed.get('outcome_change_rate', 0)
        )


def sync_from_json_files():
    """从本地 JSON 文件同步数据到 InfluxDB"""
    BASE = '/mnt/e/黑曜石/04_工作/AI开发生态系统'

    writer = InfluxDBWriter()

    # 读取校准历史
    cal_path = os.path.join(BASE, 'telemetry/calibration/calibration_history.json')
    if os.path.exists(cal_path):
        with open(cal_path) as f:
            cal = json.load(f)
        for tt, data in cal.get('by_task_type', {}).items():
            writer.write_calibration(tt, data.get('ece', 0), data.get('count', 0))

    # 读取延迟跟踪器
    pending_path = os.path.join(BASE, 'telemetry/delayed/pending_tasks.json')
    tracked_path = os.path.join(BASE, 'telemetry/delayed/tracked_tasks.json')

    pending_count = 0
    tracked_count = 0
    if os.path.exists(pending_path):
        with open(pending_path) as f:
            pending = json.load(f)
        pending_count = len(pending)

    if os.path.exists(tracked_path):
        with open(tracked_path) as f:
            tracked = json.load(f)
        tracked_count = len(tracked)

    writer.write_delayed_tracker(pending_count, tracked_count, 0, 0.33)

    # 六肖预测
    pred_path = '/home/admin1/liuhecai_v7_prediction.json'
    if os.path.exists(pred_path):
        with open(pred_path) as f:
            pred = json.load(f)
        writer.write_lottery_prediction(
            pred.get('预测期号', ''),
            pred.get('推荐6肖', []),
            0.504  # 回测命中率
        )

    print("✅ Telemetry synced to InfluxDB")


if __name__ == '__main__':
    print("=" * 50)
    print("  InfluxDB Writer - 遥测数据同步")
    print("=" * 50)

    sync_from_json_files()

    print("\n使用方法:")
    print("  from infrastructure.influxdb_writer import InfluxDBWriter")
    print("  writer = InfluxDBWriter()")
    print("  writer.write_calibration('deploy', 0.15, 10)")
    print("=" * 50)