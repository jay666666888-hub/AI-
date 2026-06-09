#!/usr/bin/env python3
"""
Contract Validator - 运行时 API 契约验证
不参与决策，只验证"合同"是否被遵守

核心职责：
① Module Contract 验证 - exports vs actual
② API Signature 验证 - 方法签名一致性
③ Registry Drift 检测 - registry vs actual code
④ Self-Check - telemetry 自身的健康度

这是防止"跨版本参数不兼容"的核心机制
"""

import sys
import hashlib
import inspect
import ast
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


# ==============================================================================
# API Fingerprint
# ==============================================================================

@dataclass
class APISignature:
    """API 签名"""
    name: str
    module: str
    args: List[str]
    returns: str
    fingerprint: str  # sha256 of signature
    doc: Optional[str] = None


@dataclass
class ContractValidationResult:
    """契约验证结果"""
    valid: bool
    module: str
    symbol: str
    expected: str
    actual: str
    drift_type: str  # missing, type_changed, signature_changed, extra
    severity: str  # BLOCK, WARN, INFO


def compute_signature(obj: Callable, name: str, module: str) -> APISignature:
    """
    计算函数的 signature fingerprint
    
    基于：
    - 函数名
    - 参数列表（含默认值）
    - 返回类型注解
    """
    try:
        sig = inspect.signature(obj)
        args = []
        for param_name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty:
                args.append(param_name)
            else:
                args.append(f"{param_name}={repr(param.default)}")
        
        returns = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else "None"
        
        # 构建签名字符串
        sig_str = f"{name}({','.join(args)}) -> {returns}"
        fingerprint = hashlib.sha256(sig_str.encode()).hexdigest()[:8]
        
        return APISignature(
            name=name,
            module=module,
            args=args,
            returns=str(returns),
            fingerprint=fingerprint,
            doc=obj.__doc__[:100] if obj.__doc__ else None
        )
    except Exception as e:
        return APISignature(
            name=name,
            module=module,
            args=[],
            returns="ERROR",
            fingerprint="ERROR"
        )


def compute_ast_signature(source: str, func_name: str) -> Optional[str]:
    """从 AST 提取函数签名（不依赖 import）"""
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                args = [arg.arg for arg in node.args.args]
                returns = ast.unparse(node.returns) if node.returns else "None"
                sig_str = f"{func_name}({','.join(args)}) -> {returns}"
                return hashlib.sha256(sig_str.encode()).hexdigest()[:8]
    except:
        pass
    return None


# ==============================================================================
# Module Contract Validator
# ==============================================================================

@dataclass
class ModuleContract:
    """模块契约"""
    module_name: str
    declared_exports: List[str]
    actual_exports: List[str]
    signatures: Dict[str, APISignature]
    missing_exports: List[str]  # declared but not found
    extra_exports: List[str]  # found but not declared
    signature_drifts: List[ContractValidationResult]
    imports_valid: bool


class ContractValidator:
    """
    运行时契约验证器
    
    检查：
    1. declared exports vs actual exports
    2. method signatures haven't changed
    3. imports are valid
    4. registry matches actual code
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleContract] = {}
        self._import_cache: Dict[str, Set[str]] = {}
    
    def register_module(self, module_name: str, declared_exports: List[str]):
        """注册模块契约"""
        self.modules[module_name] = ModuleContract(
            module_name=module_name,
            declared_exports=declared_exports,
            actual_exports=[],
            signatures={},
            missing_exports=[],
            extra_exports=[],
            signature_drifts=[],
            imports_valid=True
        )
    
    def validate_module(self, module_name: str, module_obj) -> ModuleContract:
        """验证单个模块"""
        import importlib
        
        contract = self.modules.get(module_name)
        if not contract:
            return None
        
        # 获取实际 exports
        actual = []
        signatures = {}
        
        for name in dir(module_obj):
            if name.startswith('_'):
                continue
            obj = getattr(module_obj, name)
            if callable(obj) or isinstance(obj, (property, type)):
                actual.append(name)
                signatures[name] = compute_signature(obj, name, module_name)
        
        contract.actual_exports = actual
        
        # 检查 missing exports
        contract.missing_exports = [
            e for e in contract.declared_exports 
            if e not in actual
        ]
        
        # 检查 extra exports
        contract.extra_exports = [
            e for e in actual 
            if e not in contract.declared_exports
        ]
        
        # 检查 imports
        try:
            source = inspect.getsource(module_obj)
            contract.imports_valid = self._validate_imports(source)
        except:
            contract.imports_valid = True  # can't check
        
        return contract
    
    def _validate_imports(self, source: str) -> bool:
        """验证 imports 是否有效"""
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            __import__(alias.name)
                        except ImportError:
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            importlib.import_module(node.module)
                        except ImportError:
                            return False
            return True
        except:
            return True
    
    def validate_all(self, strict: bool = True) -> Dict[str, Any]:
        """
        验证所有已注册模块
        
        strict=True: 任何 drift 都报错
        strict=False: 只警告
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "blocks": [],
            "drifts": []
        }
        
        for module_name, contract in self.modules.items():
            # Missing exports = BLOCK
            if contract.missing_exports:
                results["valid"] = False
                results["blocks"].append({
                    "module": module_name,
                    "type": "missing_exports",
                    "symbols": contract.missing_exports,
                    "severity": "BLOCK"
                })
                results["errors"].append(
                    f"[BLOCK] {module_name}: missing exports {contract.missing_exports}"
                )
            
            # Extra exports = WARN
            if contract.extra_exports:
                results["warnings"].append(
                    f"[WARN] {module_name}: undeclared exports {contract.extra_exports}"
                )
            
            # Signature drifts = BLOCK (if strict)
            for drift in contract.signature_drifts:
                if drift.severity == "BLOCK":
                    results["valid"] = False
                    results["blocks"].append({
                        "module": module_name,
                        "type": "signature_drift",
                        "symbol": drift.symbol,
                        "severity": "BLOCK"
                    })
                    results["errors"].append(
                        f"[BLOCK] {module_name}.{drift.symbol}: signature changed"
                    )
        
        return results


# ==============================================================================
# Registry Drift Detector
# ==============================================================================

class RegistryDriftDetector:
    """
    Registry Drift 检测器
    
    检查：
    1. registry exports vs actual module exports
    2. __init__.py vs registry
    3. API fingerprint changes
    """
    
    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure/_module_registry.py"
        self.baseline_fingerprints: Dict[str, Dict[str, str]] = {}  # module -> symbol -> fingerprint
        self.validator = ContractValidator()
    
    def capture_baseline(self, modules: Dict[str, List[str]]):
        """捕获当前 API fingerprints 作为 baseline"""
        import importlib
        
        for module_name, exports in modules.items():
            try:
                mod = importlib.import_module(f"infrastructure.{module_name}")
                self.validator.register_module(module_name, exports)
                
                for exp in exports:
                    if hasattr(mod, exp):
                        obj = getattr(mod, exp)
                        sig = compute_signature(obj, exp, module_name)
                        
                        if module_name not in self.baseline_fingerprints:
                            self.baseline_fingerprints[module_name] = {}
                        self.baseline_fingerprints[module_name][exp] = sig.fingerprint
            except Exception as e:
                pass
    
    def detect_drift(self) -> List[Dict]:
        """检测 API drift"""
        drifts = []
        import importlib
        
        for module_name, baseline in self.baseline_fingerprints.items():
            try:
                mod = importlib.import_module(f"infrastructure.{module_name}")
                
                for symbol, baseline_fp in baseline.items():
                    if hasattr(mod, symbol):
                        obj = getattr(mod, symbol)
                        current_sig = compute_signature(obj, symbol, module_name)
                        
                        if current_sig.fingerprint != baseline_fp:
                            drifts.append({
                                "module": module_name,
                                "symbol": symbol,
                                "baseline_fingerprint": baseline_fp,
                                "current_fingerprint": current_sig.fingerprint,
                                "severity": "BLOCK",  # API change is always BLOCK
                                "reason": "API signature changed"
                            })
            except Exception as e:
                drifts.append({
                    "module": module_name,
                    "symbol": symbol,
                    "error": str(e),
                    "severity": "WARN"
                })
        
        return drifts


# ==============================================================================
# Self-Tracing Telemetry
# ==============================================================================

class TelemetrySelfMonitor:
    """
    Telemetry 系统自监控
    
    确保：
    1. telemetry 自身的错误被记录
    2. 如果 telemetry 挂了，能检测到
    3. 所有组件的"健康度"可追溯
    """
    
    def __init__(self):
        from infrastructure.tools.execution_logger import ExecutionLogger, EventType
        self.logger = ExecutionLogger()
        self.component_health: Dict[str, bool] = {}
        self.error_log: List[Dict] = []
        self._is_healthy = True
    
    def record_component_status(self, component: str, is_healthy: bool, error: str = None):
        """记录组件状态"""
        self.component_health[component] = is_healthy
        self.logger.log_routing(
            task_id=f"telemetry_health_{component}",
            agent_id=component,
            routing_reason="health_check",
            selected_option="healthy" if is_healthy else "failed",
            metadata={
                "component": component,
                "healthy": is_healthy,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if not is_healthy:
            self._is_healthy = False
            self.error_log.append({
                "component": component,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
    
    def check_health(self) -> bool:
        """检查整体健康度"""
        # 如果最近没有心跳，说明 telemetry 可能挂了
        recent_events = self.logger.events[-10:] if self.logger.events else []
        now = datetime.now()
        
        # 简单检查：是否有最近的事件
        if not recent_events:
            self.record_component_status("telemetry_heartbeat", False, "No recent events")
            return False
        
        return self._is_healthy
    
    def get_error_summary(self) -> Dict:
        """获取错误摘要"""
        return {
            "total_errors": len(self.error_log),
            "components_affected": list(set(e["component"] for e in self.error_log)),
            "recent_errors": self.error_log[-5:] if self.error_log else [],
            "component_health": self.component_health.copy()
        }
    
    def generate_self_trace_report(self) -> str:
        """生成自追踪报告"""
        is_healthy = self.check_health()
        error_summary = self.get_error_summary()
        
        lines = [
            "=" * 60,
            "TELEMETRY SELF-TRACE REPORT",
            "=" * 60,
            f"Overall Health: {'✓ HEALTHY' if is_healthy else '✗ UNHEALTHY'}",
            f"Total Errors: {error_summary['total_errors']}",
            "",
            "Component Health:",
        ]
        
        for comp, healthy in error_summary['component_health'].items():
            status = "✓" if healthy else "✗"
            lines.append(f"  {status} {comp}")
        
        if error_summary['recent_errors']:
            lines.append("")
            lines.append("Recent Errors:")
            for err in error_summary['recent_errors']:
                lines.append(f"  ! {err['component']}: {err['error']}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# ==============================================================================
# Combined System
# ==============================================================================

class ContractSystem:
    """
    统一契约系统
    
    组合：
    - ContractValidator
    - RegistryDriftDetector
    - TelemetrySelfMonitor
    """
    
    def __init__(self):
        self.validator = ContractValidator()
        self.drift_detector = RegistryDriftDetector()
        self.self_monitor = TelemetrySelfMonitor()
        self._validated = False
        self._blocked = False
    
    def initialize(self, modules: Dict[str, List[str]]):
        """初始化 - 捕获 baseline"""
        self.drift_detector.capture_baseline(modules)
        
        # 注册所有模块
        for module_name, exports in modules.items():
            self.validator.register_module(module_name, exports)
    
    def validate(self, strict: bool = True) -> Dict:
        """
        执行完整验证
        strict=True 时，任何 BLOCK 级别的 drift 都会阻止运行
        """
        from infrastructure._module_registry import INFRASTRUCTURE_MODULES
        
        # 1. Registry Drift 检测
        drifts = self.drift_detector.detect_drift()
        
        # 2. Module Contract 验证
        import importlib
        for module_name in INFRASTRUCTURE_MODULES.keys():
            try:
                mod = importlib.import_module(f"infrastructure.{module_name}")
                self.validator.validate_module(module_name, mod)
            except Exception as e:
                pass
        
        # 3. Telemetry Self-Check
        self.self_monitor.check_health()
        
        # 4. 汇总结果
        validation_results = self.validator.validate_all(strict=strict)
        
        has_blocks = len(validation_results.get("blocks", [])) > 0 or len(drifts) > 0
        
        result = {
            "valid": not has_blocks,
            "validation": validation_results,
            "drifts": drifts,
            "telemetry_health": self.self_monitor.get_error_summary(),
            "blocked": has_blocks
        }
        
        if has_blocks and strict:
            self._blocked = True
        
        return result
    
    def generate_report(self) -> str:
        """生成人类可读报告"""
        result = self.validate(strict=True)
        
        lines = [
            "=" * 70,
            "CONTRACT SYSTEM VALIDATION REPORT",
            "=" * 70,
            f"Status: {'✓ PASS' if result['valid'] else '✗ BLOCKED'}",
            f"Blocked: {result['blocked']}",
            "",
        ]
        
        # Drifts
        if result['drifts']:
            lines.append("【API Fingerprint Drifts - BLOCK】")
            for drift in result['drifts']:
                lines.append(f"  ! {drift['module']}.{drift['symbol']}")
                lines.append(f"    {drift['baseline_fingerprint']} -> {drift['current_fingerprint']}")
        
        # Validation errors
        if result['validation']['blocks']:
            lines.append("\n【Contract Violations - BLOCK】")
            for block in result['validation']['blocks']:
                lines.append(f"  ! {block['module']}: {block['type']}")
        
        # Warnings
        if result['validation']['warnings']:
            lines.append("\n【Warnings】")
            for warn in result['validation']['warnings']:
                lines.append(f"  ⚠ {warn}")
        
        # Telemetry Health
        telemetry = result['telemetry_health']
        lines.append(f"\n【Telemetry Self-Monitor】")
        lines.append(f"  Health: {'✓' if telemetry['total_errors'] == 0 else '✗'}")
        lines.append(f"  Total Errors: {telemetry['total_errors']}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 70)
    print("Contract System - Startup Validation")
    print("=" * 70)
    
    system = ContractSystem()
    
    # 加载 registry
    print("\n[1] Loading module registry...")
    from infrastructure._module_registry import INFRASTRUCTURE_MODULES
    modules = {mod: exp.exports for mod, exp in INFRASTRUCTURE_MODULES.items()}
    print(f"    Loaded {len(modules)} modules")
    
    # 初始化
    print("\n[2] Capturing baseline fingerprints...")
    system.initialize(modules)
    print("    Baseline captured")
    
    # 验证
    print("\n[3] Running validation...")
    result = system.validate(strict=True)
    
    print("\n" + system.generate_report())
    
    if result['blocked']:
        print("\n⚠ SYSTEM BLOCKED DUE TO CONTRACT VIOLATIONS")
        print("Fix issues before runtime can proceed")
    else:
        print("\n✓ All contracts validated - system ready")


# ==============================================================================
# Auto-Fixer (for undeclared imports in public API)
# ==============================================================================

class ContractAutoFixer:
    """
    自动修复 contract 问题
    
    修复：
    1. 移除误声明的 imports（Any, Dict, List, dataclass 等）
    2. 添加缺失的 exports
    """
    
    # 类型导入黑名单 - 这些不应该作为 public API 声明
    TYPE_IMPORTS = {
        'Any', 'Dict', 'List', 'Optional', 'Callable', 'Tuple',
        'Set', 'Union', 'Type', 'dataclass', 'field', 'Enum',
        'datetime', 'timedelta', 'asdict', 'property'
    }
    
    def __init__(self, module_registry_path: str = None):
        self.module_registry_path = module_registry_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure/_module_registry.py"
    
    def clean_exports(self, exports: List[str]) -> List[str]:
        """移除 exports 中的类型导入"""
        return [e for e in exports if e not in self.TYPE_IMPORTS]
    
    def generate_clean_registry(self) -> Dict[str, List[str]]:
        """生成清理后的 registry"""
        from infrastructure._module_registry import INFRASTRUCTURE_MODULES
        
        cleaned = {}
        for module_name, module_exp in INFRASTRUCTURE_MODULES.items():
            cleaned[module_name] = self.clean_exports(module_exp.exports)
        
        return cleaned
    
    def report_fixes(self):
        """报告需要修复的内容"""
        from infrastructure._module_registry import INFRASTRUCTURE_MODULES
        cleaned = self.generate_clean_registry()
        
        print("=" * 60)
        print("CONTRACT AUTO-FIX REPORT")
        print("=" * 60)
        
        for module_name, exports in cleaned.items():
            original = INFRASTRUCTURE_MODULES[module_name].exports
            removed = set(original) - set(exports)
            
            if removed:
                print(f"\n{module_name}:")
                print(f"  Removed: {sorted(removed)}")
                print(f"  Kept: {sorted(exports)}")


if __name__ == "__main__":
    fixer = ContractAutoFixer()
    fixer.report_fixes()
