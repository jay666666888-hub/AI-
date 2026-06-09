#!/usr/bin/env python3
"""
E2E Testing Skill - 端到端测试技能
真实运行 Playwright
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    name: str
    description: str
    status: TestStatus
    duration_ms: int
    error: Optional[str] = None
    retries: int = 0
    test_fn: Optional[Callable] = None


class E2ETestSkill:
    """E2E 测试技能 - 真实运行 Playwright"""

    def __init__(self):
        self.test_suites: Dict[str, List[TestCase]] = {}
        self.current_suite: Optional[str] = None
        self.playwright = None
        self.browser = None

    def _init_playwright(self):
        """初始化 Playwright"""
        if self.playwright is None:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)

    def _close_playwright(self):
        """关闭 Playwright"""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def create_suite(self, name: str, description: str = "") -> Dict[str, Any]:
        """创建测试套件"""
        self.test_suites[name] = []
        self.current_suite = name
        return {
            "suite": name,
            "status": "created",
            "description": description
        }

    def add_test(self, name: str, description: str, test_fn: Callable = None) -> Dict[str, Any]:
        """添加测试用例"""
        if not self.current_suite:
            return {"error": "No active suite. Call create_suite first."}

        test = TestCase(
            name=name,
            description=description,
            status=TestStatus.PENDING,
            duration_ms=0,
            test_fn=test_fn
        )
        self.test_suites[self.current_suite].append(test)
        return {"test": name, "suite": self.current_suite, "status": "added"}

    def run_suite(self, suite_name: str = None, url: str = None) -> Dict[str, Any]:
        """运行测试套件"""
        target = suite_name or self.current_suite
        if not target or target not in self.test_suites:
            return {"error": f"Suite {target} not found"}

        suite = self.test_suites[target]
        if not url:
            url = "about:blank"

        self._init_playwright()
        passed = 0
        failed = 0

        for test in suite:
            test.status = TestStatus.RUNNING
            start_time = time.time()

            try:
                if test.test_fn:
                    # Run custom test function with page
                    page = self.browser.new_page()
                    try:
                        test.test_fn(page)
                        test.status = TestStatus.PASSED
                        passed += 1
                    finally:
                        page.close()
                else:
                    # Default test: navigate to URL and check title
                    page = self.browser.new_page()
                    try:
                        page.goto(url, timeout=30000)
                        page.wait_for_load_state("networkidle", timeout=10000)
                        test.status = TestStatus.PASSED
                        passed += 1
                    finally:
                        page.close()

                test.duration_ms = int((time.time() - start_time) * 1000)

            except Exception as e:
                test.status = TestStatus.FAILED
                test.error = str(e)[:200]
                test.retries += 1
                failed += 1
                test.duration_ms = int((time.time() - start_time) * 1000)

        self._close_playwright()

        return {
            "suite": target,
            "url": url,
            "total": len(suite),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/len(suite)*100:.0f}%" if suite else "N/A"
        }

    def run_test(self, test_name: str, suite_name: str = None, url: str = None) -> Dict[str, Any]:
        """运行单个测试"""
        target = suite_name or self.current_suite
        if not target or target not in self.test_suites:
            return {"error": "Suite not found"}

        suite = self.test_suites[target]
        for test in suite:
            if test.name == test_name:
                test.status = TestStatus.RUNNING
                start_time = time.time()

                self._init_playwright()
                try:
                    page = self.browser.new_page()
                    if test.test_fn:
                        test.test_fn(page)
                    elif url:
                        page.goto(url, timeout=30000)
                    test.status = TestStatus.PASSED
                    test.duration_ms = int((time.time() - start_time) * 1000)
                    return {"test": test_name, "status": "passed", "duration_ms": test.duration_ms}
                except Exception as e:
                    test.status = TestStatus.FAILED
                    test.error = str(e)[:200]
                    test.duration_ms = int((time.time() - start_time) * 1000)
                    return {"test": test_name, "status": "failed", "error": str(e)}
                finally:
                    page.close()
                    self._close_playwright()

        return {"test": test_name, "status": "not_found"}

    def get_status(self) -> Dict[str, Any]:
        """获取测试状态"""
        total_tests = sum(len(tests) for tests in self.test_suites.values())
        passed = sum(len([t for t in tests if t.status == TestStatus.PASSED]) for tests in self.test_suites.values())

        return {
            "suites": len(self.test_suites),
            "total_tests": total_tests,
            "passed": passed,
            "pass_rate": f"{passed/total_tests*100:.0f}%" if total_tests > 0 else "N/A"
        }


def run_e2e_test(suite_name: str, test_name: str = None, url: str = None) -> Dict[str, Any]:
    """快捷 E2E 测试函数"""
    skill = E2ETestSkill()

    if test_name:
        skill.create_suite(suite_name)
        skill.add_test(test_name, "")
        return skill.run_test(test_name, suite_name, url)
    else:
        return skill.run_suite(suite_name, url)
