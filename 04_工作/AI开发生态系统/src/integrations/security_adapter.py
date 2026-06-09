#!/usr/bin/env python3
"""
Security Adapter - 安全合规层集成 v2.0
L8 安全合规层 - 真实集成 ggshield/semgrep
"""

import subprocess
import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys


@dataclass
class SecurityFinding:
    """安全问题发现"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    file: str
    line: int
    content: str
    tool: str  # ggshield, semgrep, trivy


class SecurityAdapter:
    """安全扫描统一接口"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.ggshield = GGShieldAdapter(self.project_path)
        self.semgrep = SemgrepAdapter(self.project_path)

    def scan_all(self, target: str = None) -> Dict[str, Any]:
        """执行所有安全扫描"""
        target = target or self.project_path

        results = {
            "ggshield": self.ggshield.scan_path(target),
            "semgrep": self.semgrep.scan(target)
        }

        # 处理 skipped 状态
        ggshield_skipped = results["ggshield"].get("skipped", False)
        semgrep_skipped = results.get("semgrep", {}).get("skipped", False)

        # 合并发现
        all_findings = []
        if not ggshield_skipped:
            all_findings.extend(self._parse_ggshield_results(results["ggshield"]))
        if not semgrep_skipped:
            all_findings.extend(self._parse_semgrep_results(results["semgrep"]))

        return {
            "success": len(all_findings) == 0 and not ggshield_skipped and not semgrep_skipped,
            "skipped": ggshield_skipped or semgrep_skipped,
            "skipped_reason": self._get_skipped_reason(results),
            "total_findings": len(all_findings),
            "findings": all_findings,
            "by_severity": self._group_by_severity(all_findings) if not ggshield_skipped and not semgrep_skipped else {},
            "details": results
        }

    def _get_skipped_reason(self, results: Dict) -> str:
        """获取跳过的原因"""
        reasons = []
        if results.get("ggshield", {}).get("skipped"):
            reasons.append(f"ggshield: {results['ggshield'].get('reason', 'unknown')}")
        if results.get("semgrep", {}).get("skipped"):
            reasons.append(f"semgrep: {results['semgrep'].get('reason', 'unknown')}")
        return "; ".join(reasons) if reasons else ""

    def scan_code(self, target: str = None) -> Dict[str, Any]:
        """扫描代码安全问题"""
        target = target or self.project_path
        return self.semgrep.scan(target)

    def scan_secrets(self, target: str = None) -> Dict[str, Any]:
        """扫描秘钥泄露"""
        target = target or self.project_path
        return self.ggshield.scan_path(target)

    def _parse_ggshield_results(self, result: Dict) -> List[SecurityFinding]:
        """解析 ggshield 结果"""
        findings = []
        if result.get("success") and "output" in result:
            # 尝试解析 JSON 输出
            try:
                data = json.loads(result["output"])
                for incident in data.get("incidents", []):
                    findings.append(SecurityFinding(
                        severity="CRITICAL",
                        title=incident.get("name", "Secret Detected"),
                        file=incident.get("file", "unknown"),
                        line=incident.get("line", 0),
                        content=incident.get("raw", ""),
                        tool="ggshield"
                    ))
            except (json.JSONDecodeError, AttributeError):
                pass
        elif not result.get("success") and "incidents" in result:
            for incident in result.get("incidents", []):
                findings.append(SecurityFinding(
                    severity="CRITICAL",
                    title="Secret Detected",
                    file=incident.get("file", "unknown"),
                    line=incident.get("line", 0),
                    content=incident.get("raw", ""),
                    tool="ggshield"
                ))
        return findings

    def _parse_semgrep_results(self, result: Dict) -> List[SecurityFinding]:
        """解析 semgrep 结果"""
        findings = []
        if result.get("success"):
            try:
                data = json.loads(result["output"])
                for item in data.get("results", []):
                    findings.append(SecurityFinding(
                        severity=item.get("extra", {}).get("severity", "MEDIUM").upper(),
                        title=item.get("check", "Unknown"),
                        file=item.get("path", "unknown"),
                        line=item.get("start", {}).get("line", 0),
                        content=item.get("extra", {}).get("lines", ""),
                        tool="semgrep"
                    ))
            except (json.JSONDecodeError, AttributeError):
                pass
        return findings

    def _group_by_severity(self, findings: List[SecurityFinding]) -> Dict[str, List]:
        """按严重性分组"""
        grouped = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for f in findings:
            if f.severity in grouped:
                grouped[f.severity].append(f)
        return grouped

    def block_if_critical(self, scan_result: Dict) -> bool:
        """如果有严重问题则阻断"""
        critical = len(scan_result.get("by_severity", {}).get("CRITICAL", []))
        if critical > 0:
            print(f"🚨 发现 {critical} 个严重安全问题，阻断提交")
            return True
        return False


class GGShieldAdapter:
    """GitGuardian ggshield 秘钥检测"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.python = sys.executable  # 使用当前 venv 的 python

    def has_api_key(self) -> bool:
        """检查是否有 API key 配置"""
        result = subprocess.run(
            [self.python, "-m", "ggshield", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0

    def scan_path(self, path: str = None) -> Dict[str, Any]:
        """扫描路径"""
        target = path or self.project_path

        # 前置检查：API key 是否配置
        if not self.has_api_key():
            return {
                "success": False,
                "skipped": True,
                "reason": "ggshield API key not configured",
                "error": "A GitGuardian API key is needed. Run 'ggshield auth login'",
                "incidents_count": 0
            }

        try:
            result = subprocess.run(
                [self.python, "-m", "ggshield", "secret", "scan", "path", target, "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout

            # 检查是否因为 API key 失败
            if "API key is needed" in result.stderr:
                return {
                    "success": False,
                    "skipped": True,
                    "reason": "ggshield API key not configured",
                    "error": result.stderr,
                    "incidents_count": 0
                }

            try:
                data = json.loads(output)
                incidents = data.get("entities", {}).get("total_entities", 0)
            except json.JSONDecodeError:
                incidents = len([l for l in output.splitlines() if "incident" in l.lower()])

            return {
                "success": result.returncode == 0,
                "skipped": False,
                "output": output,
                "error": result.stderr,
                "incidents_count": incidents
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "skipped": False, "error": "Scan timeout", "incidents_count": 0}
        except Exception as e:
            return {"success": False, "skipped": False, "error": str(e), "incidents_count": 0}

    def scan_commit_range(self, range_str: str) -> Dict[str, Any]:
        """扫描 commit 范围"""
        try:
            result = subprocess.run(
                [self.python, "-m", "ggshield", "secret", "scan", "commit-range", range_str, "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class SemgrepAdapter:
    """Semgrep 代码安全扫描"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.python = sys.executable

    def scan(self, target: str = None, config: str = "auto") -> Dict[str, Any]:
        """扫描代码"""
        target = target or self.project_path
        try:
            result = subprocess.run(
                [self.python, "-m", "semgrep", "--json", "-c", config, target],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "success": result.returncode in (0, 1),  # 0=no findings, 1=findings
                "output": result.stdout,
                "error": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Scan timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scan_with_rules(self, target: str, rules_path: str) -> Dict[str, Any]:
        """使用指定规则扫描"""
        try:
            result = subprocess.run(
                [self.python, "-m", "semgrep", "--json", "-r", rules_path, target],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "success": result.returncode in (0, 1),
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class TrivyAdapter:
    """Trivy 容器漏洞扫描"""

    def __init__(self):
        self.path = "trivy"

    def scan_image(self, image: str, severity: str = "HIGH,CRITICAL") -> Dict[str, Any]:
        """扫描容器镜像"""
        try:
            result = subprocess.run(
                [self.path, "image", "--severity", severity, "--format", "json", image],
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class GitleaksAdapter:
    """Gitleaks Git 秘钥检测"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.path = "gitleaks"

    def scan(self, source: str = None) -> Dict[str, Any]:
        """扫描 Git 仓库"""
        target = source or self.project_path
        try:
            result = subprocess.run(
                [self.path, "scan", "-s", target, "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "success": result.returncode in (0, 1),
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("=== 安全扫描测试 ===\n")

    adapter = SecurityAdapter()

    # 扫描 src 目录
    print("扫描 src 目录...")
    result = adapter.scan_all("./src")

    print(f"成功: {result['success']}")
    print(f"发现数: {result['total_findings']}")

    by_sev = result.get("by_severity", {})
    for sev, items in by_sev.items():
        if items:
            print(f"  {sev}: {len(items)} 个")

    if result.get("findings"):
        print("\n前3个发现:")
        for f in result["findings"][:3]:
            print(f"  [{f.severity}] {f.title} @ {f.file}:{f.line}")
