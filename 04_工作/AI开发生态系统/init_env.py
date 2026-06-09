#!/usr/bin/env python3
"""
AI 开发生态系统 - 一键初始化脚本
支持: Linux/WSL (bash) / Windows (PowerShell)
"""

import os
import sys
import subprocess
import venv

def create_venv_python(venv_path: str) -> str:
    """创建虚拟环境并返回 Python 路径"""
    print(f"创建虚拟环境: {venv_path}")

    if os.path.exists(venv_path):
        print(f"  虚拟环境已存在，跳过")
    else:
        venv.create(venv_path, with_pip=True)

    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python3")

def install_deps(python_path: str) -> bool:
    """安装依赖"""
    print("\n安装依赖...")
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

    if not os.path.exists(req_file):
        print(f"  警告: {req_file} 未找到，跳过依赖安装")
        return False

    result = subprocess.run(
        [python_path, "-m", "pip", "install", "-r", req_file],
        capture_output=False
    )
    return result.returncode == 0

def run_doctor(python_path: str) -> bool:
    """运行健康检查"""
    print("\n运行健康检查...")
    doctor_script = os.path.join(os.path.dirname(__file__), "src", "ecosystem_doctor.py")

    if not os.path.exists(doctor_script):
        print(f"  警告: {doctor_script} 未找到")
        return False

    result = subprocess.run([python_path, doctor_script], capture_output=False)
    return result.returncode == 0

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(project_root, "venv")

    print("=" * 60)
    print("  AI 开发生态系统 - 初始化")
    print("=" * 60)

    python_path = create_venv_python(venv_path)
    success = install_deps(python_path)

    if success:
        print("\n" + "=" * 60)
        print("  初始化成功！")
        print("=" * 60)
        print(f"\n运行系统:")
        print(f"  Linux/WSL: {python_path} src/ecosystem_doctor.py")
        print(f"  Windows:   {python_path} src\\ecosystem_doctor.py")
    else:
        print("\n初始化完成，但依赖安装有问题")
        print("可手动运行: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
