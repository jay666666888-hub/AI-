#!/usr/bin/env python3
"""
DataOps Adapter - 数据工程层集成
L17 数据工程层
"""

import subprocess
from typing import Dict, Any, List, Optional


class AirflowAdapter:
    """Apache Airflow 数据管道编排适配器"""

    def __init__(self, web_server: str = "http://localhost:8080"):
        self.web_server = web_server
        self.cli = "airflow"

    def trigger_dag(self, dag_id: str, conf: Dict = None) -> Dict[str, Any]:
        """触发 DAG"""
        cmd = [self.cli, "dags", "trigger", dag_id]
        if conf:
            import json
            cmd.extend(["--conf", json.dumps(conf)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def list_dags(self) -> List[Dict[str, Any]]:
        """列出所有 DAG"""
        cmd = [self.cli, "dags", "list", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return []

    def pause_dag(self, dag_id: str) -> bool:
        """暂停 DAG"""
        result = subprocess.run([self.cli, "dags", "pause", dag_id],
                                capture_output=True, text=True)
        return result.returncode == 0

    def unpause_dag(self, dag_id: str) -> bool:
        """取消暂停 DAG"""
        result = subprocess.run([self.cli, "dags", "unpause", dag_id],
                                capture_output=True, text=True)
        return result.returncode == 0


class PrefectAdapter:
    """Prefect 数据流编排适配器"""

    def __init__(self, api_url: str = "http://localhost:4200"):
        self.api_url = api_url
        self.cli = "prefect"

    def deploy(self, flow_name: str, params: Dict = None) -> Dict[str, Any]:
        """部署 flow"""
        cmd = [self.cli, "deployment", "apply", f"{flow_name}-deployment.yaml"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }

    def run_flow(self, deployment_name: str, params: Dict = None) -> str:
        """运行 flow"""
        cmd = [self.cli, "deployment", "run", deployment_name]
        if params:
            for k, v in params.items():
                cmd.extend(["-p", f"{k}={v}"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # 提取 run ID
            for line in result.stdout.splitlines():
                if "Running flow" in line or "Submitted flow run" in line:
                    return line.strip()
        return ""

    def list_flows(self) -> List[Dict[str, Any]]:
        """列出 flows"""
        cmd = [self.cli, "flow", "list", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return []


class KafkaAdapter:
    """Apache Kafka 实时数据流适配器"""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.cli = "kafka-console"

    def produce(self, topic: str, messages: List[str]) -> Dict[str, Any]:
        """生产消息"""
        import subprocess
        cmd = f"echo -e " + "\\n".join(messages) + f" | {self.cli}-producer --bootstrap-server {self.bootstrap_servers} --topic {topic}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "error": result.stderr
        }

    def consume(self, topic: str, from_beginning: bool = False) -> List[str]:
        """消费消息"""
        cmd = [self.cli + "-consumer", "--bootstrap-server", self.bootstrap_servers,
               "--topic", topic]
        if from_beginning:
            cmd.append("--from-beginning")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.splitlines()
        return []


class GreatExpectationsAdapter:
    """Great Expectations 数据质量验证适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.cli = "great_expectations"

    def validate(self, expectation_suite: str,
                 batch_request: Dict) -> Dict[str, Any]:
        """验证数据"""
        cmd = [
            self.cli, "checkpoint", "run",
            f"--expectation-suite={expectation_suite}",
            "--batch-request", str(batch_request)
        ]
        result = subprocess.run(cmd, cwd=self.project_path,
                                capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }


class DBtAdapter:
    """dbt 数据转换适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()

    def compile(self) -> Dict[str, Any]:
        """编译 dbt 项目"""
        result = subprocess.run(
            ["dbt", "compile"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run(self, models: List[str] = None) -> Dict[str, Any]:
        """运行 models"""
        cmd = ["dbt", "run"]
        if models:
            cmd.extend(["--models"] + models)

        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def test(self, models: List[str] = None) -> Dict[str, Any]:
        """运行 tests"""
        cmd = ["dbt", "test"]
        if models:
            cmd.extend(["--models"] + models)

        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }