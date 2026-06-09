#!/usr/bin/env python3
"""GateGuard Skill - edit前必须收集事实"""
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    EDIT = "edit"
    WRITE = "write"
    BASH_DESTRUCTIVE = "bash_destructive"
    BASH_ROUTINE = "bash_routine"

@dataclass
class GateDecision:
    action: ActionType
    status: str
    required_facts: List[str]
    gathered_facts: List[str]
    reason: str

class GateGuardSkill:
    def __init__(self):
        self.per_file_edits = {}
        self.session_bash_gated = False

    def check_action(self, action_type: str, target: str = "") -> GateDecision:
        action = ActionType(action_type)
        if action == ActionType.EDIT:
            if self.per_file_edits.get(target):
                return GateDecision(action, "allow", [], [], "OK")
            self.per_file_edits[target] = True
            return GateDecision(action, "deny", ["imports", "affected functions", "schema"], [], "First edit")
        elif action == ActionType.WRITE:
            return GateDecision(action, "force", ["callers", "conflicts"], [], "New file")
        elif action == ActionType.BASH_DESTRUCTIVE:
            return GateDecision(action, "deny", ["what deleted", "alternatives"], [], "Dangerous")
        elif action == ActionType.BASH_ROUTINE:
            if self.session_bash_gated:
                return GateDecision(action, "allow", [], [], "OK")
            self.session_bash_gated = True
            return GateDecision(action, "force", ["verifies", "produces"], [], "Routine")
        return GateDecision(action, "allow", [], [], "OK")

    def gather_facts(self, d: GateDecision, facts: List[str]) -> GateDecision:
        d.gathered_facts = facts
        if len(facts) >= len(d.required_facts):
            d.status = "allow"
        return d

    def format_msg(self, d: GateDecision) -> str:
        if d.status == "deny":
            return f"BLOCKED: {d.action.value}\nMust gather: {d.required_facts}"
        elif d.status == "force":
            return f"FORCE: {d.action.value}\nMust answer: {d.required_facts}"
        return "ALLOWED"

    def is_allowed(self, d: GateDecision) -> bool:
        return d.status == "allow"

def run_gateguard(action_type: str, target: str = "") -> Dict[str, Any]:
    skill = GateGuardSkill()
    d = skill.check_action(action_type, target)
    return {"status": d.status, "allowed": skill.is_allowed(d), "message": skill.format_msg(d)}

if __name__ == "__main__":
    r = run_gateguard("edit", "src/main.py")
    print(r["message"])
    print(f"Allowed: {r['allowed']}")
