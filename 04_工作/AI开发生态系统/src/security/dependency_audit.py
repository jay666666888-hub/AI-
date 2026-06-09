"""
Dependency Auditor - 依赖审计
检查过时依赖、已知漏洞
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import subprocess
import json
import os


@dataclass
class Vulnerability:
    package: str
    severity: str
    vulnerability_id: str
    title: str
    current_version: str
    fixed_version: Optional[str] = None


@dataclass
class OutdatedPackage:
    package: str
    current: str
    latest: str
    wanted: str


class DependencyAuditor:
    """依赖审计器"""

    def __init__(self):
        self.language = self._detect_language()

    def _detect_language(self) -> str:
        """检测项目语言"""
        if os.path.exists("package.json"):
            return "node"
        elif os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
            return "python"
        elif os.path.exists("go.mod"):
            return "go"
        elif os.path.exists("Cargo.toml"):
            return "rust"
        return "unknown"

    def audit(self) -> Dict[str, Any]:
        """执行完整审计"""
        if self.language == "node":
            return self._audit_node()
        elif self.language == "python":
            return self._audit_python()
        elif self.language == "go":
            return self._audit_go()
        elif self.language == "rust":
            return self._audit_rust()
        return {"error": f"不支持的语言: {self.language}"}

    def _audit_node(self) -> Dict[str, Any]:
        """Node.js 依赖审计"""
        results = {"vulnerabilities": [], "outdated": []}

        # 运行 npm audit
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.stdout:
                audit_data = json.loads(result.stdout)
                if "vulnerabilities" in audit_data:
                    for pkg, info in audit_data["vulnerabilities"].items():
                        results["vulnerabilities"].append({
                            "package": pkg,
                            "severity": info.get("severity", "unknown"),
                            "title": info.get("title", ""),
                            "url": info.get("url", "")
                        })
        except FileNotFoundError:
            results["error"] = "npm 未安装"
        except subprocess.TimeoutExpired:
            results["error"] = "npm audit 超时"
        except json.JSONDecodeError:
            pass

        return results

    def _audit_python(self) -> Dict[str, Any]:
        """Python 依赖审计"""
        results = {"vulnerabilities": [], "outdated": []}

        # 检查过时包
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.stdout:
                outdated = json.loads(result.stdout)
                results["outdated"] = [
                    {"package": p["name"], "current": p["version"], "latest": p["latest_version"]}
                    for p in outdated
                ]
        except FileNotFoundError:
            results["error"] = "pip 未安装"
        except subprocess.TimeoutExpired:
            results["error"] = "pip list 超时"
        except json.JSONDecodeError:
            pass

        # 安全审计（需要 safety 或 pip-audit）
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                results["vulnerabilities"] = vulnerabilities
        except FileNotFoundError:
            pass  # safety 未安装

        return results

    def _audit_go(self) -> Dict[str, Any]:
        """Go 依赖审计"""
        results = {"vulnerabilities": [], "outdated": []}

        try:
            result = subprocess.run(
                ["go", "mod", "verify"],
                capture_output=True,
                text=True,
                timeout=60
            )
            results["verified"] = result.returncode == 0
        except FileNotFoundError:
            results["error"] = "go 未安装"

        return results

    def _audit_rust(self) -> Dict[str, Any]:
        """Rust 依赖审计"""
        results = {"vulnerabilities": [], "outdated": []}

        try:
            result = subprocess.run(
                ["cargo", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("type") == "vulnerability":
                                results["vulnerabilities"].append(data)
                        except json.JSONDecodeError:
                            pass
        except FileNotFoundError:
            results["error"] = "cargo-audit 未安装"

        return results

    def check_licenses(self, allowed: List[str] = None) -> Dict[str, Any]:
        """检查依赖许可证"""
        if allowed is None:
            allowed = ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause"]

        results = {"allowed": [], "restricted": [], "unknown": []}

        if self.language == "node":
            try:
                result = subprocess.run(
                    ["npm", "license", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.stdout:
                    licenses = json.loads(result.stdout)
                    for pkg, lic in licenses.items():
                        if lic in allowed:
                            results["allowed"].append({"package": pkg, "license": lic})
                        elif lic:
                            results["restricted"].append({"package": pkg, "license": lic})
                        else:
                            results["unknown"].append({"package": pkg})
            except Exception:
                pass

        return results


if __name__ == "__main__":
    auditor = DependencyAuditor()
    print(f"检测到语言: {auditor.language}")
    print("DependencyAuditor 已就绪")
