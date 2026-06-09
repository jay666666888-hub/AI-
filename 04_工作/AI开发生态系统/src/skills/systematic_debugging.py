#!/usr/bin/env python3
"""
Systematic Debugging Skill - 系统化调试
基于 Superpowers methodology
4 步找根因: 收集症状 → 假设原因 → 设计实验 → 定位修复
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DebugStep:
    """调试步骤"""
    step: str  # collect, hypothesize, experiment, locate, fix
    description: str
    status: str  # pending, in_progress, completed
    result: str = ""


class SystematicDebuggingSkill:
    """
    systematic-debugging skill - 系统化调试
    
    4 步流程:
    1. 收集症状 - 错误信息、堆栈、环境
    2. 假设原因 - 列出可能的原因
    3. 设计实验 - 设计验证实验
    4. 定位修复 - 找到真正原因并修复
    """

    def __init__(self):
        self.steps: List[DebugStep] = []
        self.symptoms: Dict[str, Any] = {}
        self.hypotheses: List[Dict[str, Any]] = []
        self.experiments: List[Dict[str, Any]] = []

    def collect_symptoms(self, error_info: str = None, stack_trace: str = None,
                       environment: Dict = None) -> Dict[str, Any]:
        """
        收集症状
        
        Args:
            error_info: 错误信息
            stack_trace: 堆栈信息
            environment: 环境信息 (OS, version, etc.)
        """
        self.symptoms = {
            "error_message": error_info or "",
            "stack_trace": stack_trace or "",
            "environment": environment or {},
            "reproducible": False,
            "frequency": "unknown"
        }
        
        # 更新步骤状态
        self._update_step("collect", "completed", f"收集到 {len(self.symptoms)} 项症状")
        
        return self.symptoms

    def generate_hypotheses(self) -> List[Dict[str, Any]]:
        """
        生成可能的原因假设
        """
        hypotheses = []
        
        # 基于症状分析生成假设
        if self.symptoms.get("error_message"):
            hypotheses.append({
                "id": "hyp-1",
                "description": "输入验证失败 - 外部数据未正确处理",
                "probability": "high",
                "evidence": "错误信息包含输入相关内容"
            })
            
        hypotheses.extend([
            {
                "id": "hyp-2",
                "description": "空指针/未初始化 - 对象未正确创建或赋值",
                "probability": "medium",
                "evidence": "常见编程错误"
            },
            {
                "id": "hyp-3",
                "description": "配置错误 - 环境变量或配置文件问题",
                "probability": "medium",
                "evidence": "需要检查配置"
            },
            {
                "id": "hyp-4",
                "description": "并发问题 - 多线程/异步竞态条件",
                "probability": "low",
                "evidence": "需要检查并发代码"
            },
            {
                "id": "hyp-5",
                "description": "依赖问题 - 第三方库版本不兼容",
                "probability": "low",
                "evidence": "需要检查依赖版本"
            }
        ])
        
        self.hypotheses = hypotheses
        self._update_step("hypothesize", "completed", f"生成了 {len(hypotheses)} 个假设")
        
        return hypotheses

    def design_experiment(self, hypothesis_id: str, test_plan: str) -> Dict[str, Any]:
        """
        设计验证实验
        
        Args:
            hypothesis_id: 要验证的假设 ID
            test_plan: 实验计划
        """
        experiment = {
            "id": f"exp-{len(self.experiments) + 1}",
            "hypothesis_id": hypothesis_id,
            "test_plan": test_plan,
            "status": "pending"
        }
        self.experiments.append(experiment)
        
        return experiment

    def locate_root_cause(self) -> Optional[Dict[str, Any]]:
        """
        定位根因 - 基于实验结果
        """
        for exp in self.experiments:
            if exp["status"] == "verified":
                # 找到对应的假设
                for hyp in self.hypotheses:
                    if hyp["id"] == exp["hypothesis_id"]:
                        hyp["verified"] = True
                        return hyp
        
        return None

    def fix_and_verify(self, root_cause: Dict, fix_description: str) -> Dict[str, Any]:
        """
        修复并验证
        """
        self._update_step("fix", "completed", fix_description)
        
        return {
            "root_cause": root_cause,
            "fix_description": fix_description,
            "verified": False  # 需要实际运行验证
        }

    def _update_step(self, step: str, status: str, result: str = "") -> None:
        """更新步骤状态"""
        step_names = {
            "collect": "收集症状",
            "hypothesize": "假设原因",
            "experiment": "设计实验",
            "locate": "定位根因",
            "fix": "修复验证"
        }
        
        # 找到或创建步骤
        found = False
        for s in self.steps:
            if s.step == step:
                s.status = status
                s.result = result
                found = True
                break
        
        if not found:
            self.steps.append(DebugStep(
                step=step,
                description=step_names.get(step, step),
                status=status,
                result=result
            ))

    def get_progress(self) -> str:
        """获取调试进度"""
        output = "🔍 调试进度:\n\n"
        for s in self.steps:
            status_icon = {"pending": "⬜", "in_progress": "🔄", "completed": "✅"}.get(s.status, "⬜")
            output += f"{status_icon} {s.description}"
            if s.result:
                output += f" → {s.result}"
            output += "\n"
        return output

    def run(self, error_info: str = None, stack_trace: str = None,
            environment: Dict = None) -> Dict[str, Any]:
        """运行完整调试流程"""
        # Step 1: 收集症状
        symptoms = self.collect_symptoms(error_info, stack_trace, environment)
        
        # Step 2: 生成假设
        hypotheses = self.generate_hypotheses()
        
        # Step 3: 设计实验
        for hyp in hypotheses[:3]:  # 只验证前 3 个最可能的
            exp = self.design_experiment(
                hyp["id"],
                f"设计实验验证假设: {hyp['description']}"
            )
        
        return {
            "status": "hypotheses_ready",
            "symptoms": symptoms,
            "hypotheses": hypotheses,
            "experiments": self.experiments,
            "progress": self.get_progress(),
            "message": self.get_progress()
        }


def run_debugging(error_info: str = None, stack_trace: str = None) -> Dict[str, Any]:
    """快捷函数"""
    skill = SystematicDebuggingSkill()
    return skill.run(error_info, stack_trace)


if __name__ == "__main__":
    result = run_debugging("NameError: name 'x' is not defined", "line 10 in main()")
    print(result["message"])
