"""
Vulnerability Scanner - 漏洞扫描器
集成 zizmor (GitHub Actions 安全) 等工具
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import subprocess
import os


@dataclass
class Vulnerability:
    id: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    recommendation: Optional[str] = None


class VulnerabilityScanner:
    """漏洞扫描器"""

    def __init__(self):
        self.findings: List[Vulnerability] = []

    def scan_file(self, file_path: str) -> List[Vulnerability]:
        """扫描单个文件"""
        findings = []
        ext = os.path.splitext(file_path)[1].lower()

        scanners = {
            ".py": self._scan_python,
            ".js": self._scan_javascript,
            ".ts": self._scan_typescript,
            ".yml": self._scan_github_actions,
            ".yaml": self._scan_github_actions,
        }

        scanner = scanners.get(ext)
        if scanner:
            findings = scanner(file_path)

        return findings

    def scan_directory(self, dir_path: str, patterns: List[str] = None) -> Dict[str, Any]:
        """扫描目录"""
        if patterns is None:
            patterns = ["*.py", "*.js", "*.ts", "*.yml", "*.yaml"]

        all_findings = []
        for pattern in patterns:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if os.path.match(pattern, file):
                        file_path = os.path.join(root, file)
                        findings = self.scan_file(file_path)
                        all_findings.extend(findings)

        return {
            "total_files_scanned": len(set(os.path.dirname(f.file) for f in all_findings if f.file)),
            "total_vulnerabilities": len(all_findings),
            "by_severity": self._count_by_severity(all_findings),
            "findings": all_findings
        }

    def _scan_python(self, file_path: str) -> List[Vulnerability]:
        """Python 安全扫描"""
        findings = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        import re
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']{8,}', '硬编码API密钥'),
            (r'secret\s*=\s*["\'][^"\']{8,}', '硬编码密钥'),
            (r'password\s*=\s*["\'][^"\']{8,}', '硬编码密码'),
            (r'token\s*=\s*["\'][^"\']{8,}', '硬编码令牌'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(Vulnerability(
                        id="SEC-001",
                        severity="critical",
                        title=f"硬编码敏感信息: {desc}",
                        description=f"在第{i}行发现硬编码敏感信息",
                        file=file_path,
                        line=i,
                        recommendation="使用环境变量或密钥管理服务"
                    ))

        dangerous_patterns = [
            (r'\beval\s*\(', '使用eval()', 'critical', 'eval()可执行任意代码'),
            (r'\bexec\s*\(', '使用exec()', 'critical', 'exec()可执行任意代码'),
            (r'pickle\.loads?', '使用pickle', 'high', 'pickle可能反序列化恶意数据'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc, severity, rec in dangerous_patterns:
                if re.search(pattern, line):
                    findings.append(Vulnerability(
                        id="SEC-002",
                        severity=severity,
                        title=f"危险函数: {desc}",
                        description=f"在第{i}行使用{desc}",
                        file=file_path,
                        line=i,
                        recommendation=rec
                    ))

        return findings

    def _scan_javascript(self, file_path: str) -> List[Vulnerability]:
        """JavaScript 安全扫描"""
        findings = []

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')

        import re
        dangerous_patterns = [
            (r'\beval\s*\(', '使用eval()', 'critical'),
            (r'innerHTML\s*=', 'innerHTML赋值', 'high'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc, severity in dangerous_patterns:
                if re.search(pattern, line):
                    findings.append(Vulnerability(
                        id="JS-001",
                        severity=severity,
                        title=f"潜在XSS: {desc}",
                        description=f"在第{i}行发现{desc}",
                        file=file_path,
                        line=i,
                        recommendation="净化用户输入"
                    ))

        return findings

    def _scan_typescript(self, file_path: str) -> List[Vulnerability]:
        """TypeScript 安全扫描"""
        return self._scan_javascript(file_path)

    def _scan_github_actions(self, file_path: str) -> List[Vulnerability]:
        """GitHub Actions 安全扫描"""
        findings = []

        try:
            result = subprocess.run(["zizmor", file_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return findings
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            return findings

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')

        import re
        for i, line in enumerate(lines, 1):
            if re.search(r'pull_request_target', line, re.IGNORECASE):
                findings.append(Vulnerability(
                    id="GHA-001",
                    severity="high",
                    title="pull_request_target事件",
                    description=f"在第{i}行发现安全问题",
                    file=file_path,
                    line=i,
                    recommendation="使用pull_request事件代替"
                ))

        return findings

    def _count_by_severity(self, findings: List[Vulnerability]) -> Dict[str, int]:
        return {
            "critical": len([f for f in findings if f.severity == "critical"]),
            "high": len([f for f in findings if f.severity == "high"]),
            "medium": len([f for f in findings if f.severity == "medium"]),
            "low": len([f for f in findings if f.severity == "low"]),
        }


if __name__ == "__main__":
    scanner = VulnerabilityScanner()
    print("VulnerabilityScanner 已就绪")
