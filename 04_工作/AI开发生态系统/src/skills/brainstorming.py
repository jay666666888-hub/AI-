#!/usr/bin/env python3
"""
Brainstorming Skill - 需求澄清
基于 Superpowers methodology
自动在写代码前先问清楚问题
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ClarifyingQuestion:
    """澄清问题"""
    question: str
    topic: str  # scope, tech, priority, risk, other
    asked: bool = False
    answered: bool = False
    answer: str = ""


class BrainstormingSkill:
    """
    brainstorming skill - 在写代码前先理解需求
    
    工作流程:
    1. 检查项目上下文
    2. 提出澄清问题 (每次一个)
    3. 提出 2-3 种方案及其权衡
    4. 展示设计方案并获得用户批准
    5. 才能开始实现
    """

    def __init__(self):
        self.questions: List[ClarifyingQuestion] = []
        self.project_context = {}
        self.options: List[Dict[str, Any]] = []

    def check_context(self, project_path: str) -> Dict[str, Any]:
        """检查项目上下文"""
        import os
        context = {
            "files": [],
            "readme": "",
            "tech_stack": [],
            "recent_changes": []
        }

        # 读取 README
        readme_path = os.path.join(project_path, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                context["readme"] = f.read()[:500]

        # 列出源文件
        src_path = os.path.join(project_path, "src")
        if os.path.exists(src_path):
            for root, dirs, files in os.walk(src_path):
                for f in files:
                    if f.endswith((".py", ".ts", ".js", ".go")):
                        context["files"].append(os.path.join(root, f))

        self.project_context = context
        return context

    def generate_questions(self, user_input: str) -> List[ClarifyingQuestion]:
        """
        根据用户输入生成澄清问题
        
        Args:
            user_input: 用户的原始需求
            
        Returns:
            澄清问题列表
        """
        questions = []
        
        # 基础问题
        questions.append(ClarifyingQuestion(
            question="这个功能的用户是谁？有什么具体的使用场景？",
            topic="scope"
        ))
        
        # 技术问题
        questions.append(ClarifyingQuestion(
            question="有没有特定的技术栈要求？需要和现有系统集成吗？",
            topic="tech"
        ))
        
        # 优先级问题
        questions.append(ClarifyingQuestion(
            question="这个功能的优先级是什么？有没有截止日期？",
            topic="priority"
        ))
        
        # 风险问题
        questions.append(ClarifyingQuestion(
            question="有什么已知的风险或限制条件吗？",
            topic="risk"
        ))
        
        self.questions = questions
        return questions

    def propose_options(self, requirement: str) -> List[Dict[str, Any]]:
        """
        提出 2-3 种方案及权衡
        
        Returns:
            方案列表，每项包含 name, pros, cons, complexity, recommended
        """
        options = [
            {
                "name": "方案 A: 快速原型法",
                "pros": "开发快，能快速验证概念",
                "cons": "代码质量可能较低，后期需要重构",
                "complexity": "低",
                "recommended": False
            },
            {
                "name": "方案 B: 渐进式开发",
                "pros": "平衡速度和质量，容易迭代",
                "cons": "需要良好的架构设计",
                "complexity": "中",
                "recommended": True
            },
            {
                "name": "方案 C: 企业级方案",
                "pros": "架构完善，易于维护扩展",
                "cons": "开发周期长，前期投入大",
                "complexity": "高",
                "recommended": False
            }
        ]
        
        self.options = options
        return options

    def format_questions_for_user(self) -> str:
        """格式化问题列表供用户回答"""
        output = "❓ 需要澄清的问题:\n\n"
        for i, q in enumerate(self.questions, 1):
            status = "✅ 已回答" if q.answered else "⬜ 待回答"
            output += f"{i}. [{status}] {q.question}\n"
            if q.answered:
                output += f"   回答: {q.answer}\n"
        return output

    def format_options_for_user(self) -> str:
        """格式化方案列表供用户选择"""
        output = "📋 可选方案:\n\n"
        for opt in self.options:
            rec = "⭐ 推荐" if opt["recommended"] else ""
            output += f"""
**{opt['name']}** {rec}
- ✅ 优点: {opt['pros']}
- ❌ 缺点: {opt['cons']}
- 📊 复杂度: {opt['complexity']}
"""
        return output

    def run(self, user_input: str, project_path: str = ".") -> Dict[str, Any]:
        """
        运行 brainstorming skill
        
        Returns:
            包含 context, questions, options, design 的字典
        """
        # 1. 检查项目上下文
        context = self.check_context(project_path)
        
        # 2. 生成澄清问题
        questions = self.generate_questions(user_input)
        
        # 3. 提出方案
        options = self.propose_options(user_input)
        
        return {
            "status": "need_clarification",
            "context": context,
            "questions": [
                {"question": q.question, "topic": q.topic, "answered": q.answered, "answer": q.answer}
                for q in self.questions
            ],
            "options": options,
            "next_step": "awaiting_user_answers",
            "message": self.format_questions_for_user() + "\n" + self.format_options_for_user()
        }

    def answer_question(self, question_index: int, answer: str) -> None:
        """记录用户回答"""
        if 0 <= question_index < len(self.questions):
            self.questions[question_index].answer = answer
            self.questions[question_index].answered = True

    def is_ready(self) -> bool:
        """检查是否所有问题都已回答"""
        return all(q.answered for q in self.questions)


def run_brainstorming(user_input: str, project_path: str = ".") -> Dict[str, Any]:
    """快捷函数"""
    skill = BrainstormingSkill()
    return skill.run(user_input, project_path)


if __name__ == "__main__":
    result = run_brainstorming("做个用户登录功能")
    print(result["message"])
