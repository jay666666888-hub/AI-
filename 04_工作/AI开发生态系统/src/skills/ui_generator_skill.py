#!/usr/bin/env python3
"""
UI Generator Skill - 前端生成层 L15 v2.0
支持 HTML/React/Vue/Tailwind 四种框架
自动保存到 generated_ui/ 目录
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import os


class UIFramework(Enum):
    HTML = "html"
    REACT = "react"
    VUE = "vue"
    TAILWIND = "tailwind"


class UIComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class UIGenerationRequest:
    description: str
    framework: UIFramework = UIFramework.HTML
    complexity: UIComplexity = UIComplexity.MEDIUM
    theme: str = "light"


class UIGeneratorSkill:
    """
    UI 生成器技能 v2.0

    支持:
    - HTML + Bootstrap
    - React + Bootstrap
    - Vue + Bootstrap
    - Tailwind CSS
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "generated_ui"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.history: List[Dict[str, Any]] = []

    def generate(self, description: str, framework: str = "html") -> Dict[str, Any]:
        """根据描述生成 UI"""
        desc_lower = description.lower()
        ui_type = self._detect_ui_type(desc_lower)
        fw = framework.lower()

        if fw == "react":
            code = self._generate_react(desc_lower, ui_type)
            ext = "jsx"
        elif fw == "vue":
            code = self._generate_vue(desc_lower, ui_type)
            ext = "vue"
        elif fw == "tailwind":
            code = self._generate_tailwind(desc_lower, ui_type)
            ext = "html"
        else:
            code = self._generate_html(desc_lower, ui_type)
            ext = "html"

        filename = f"ui_{ui_type}_{len(self.history)}.{ext}"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        result = {
            "status": "success",
            "ui_type": ui_type,
            "framework": fw,
            "code": code,
            "file_path": filepath,
            "filename": filename,
            "lines": len(code.splitlines()),
            "preview_tip": f"打开 {filepath} 预览"
        }

        self.history.append({"description": description, "ui_type": ui_type, "result": result})
        return result

    def _detect_ui_type(self, description: str) -> str:
        if any(kw in description for kw in ["仪表盘", "dashboard", "控制台", "面板", "统计"]):
            return "dashboard"
        elif any(kw in description for kw in ["表单", "form", "登录", "注册", "输入"]):
            return "form"
        elif any(kw in description for kw in ["表格", "table", "列表", "数据", "管理"]):
            return "table"
        elif any(kw in description for kw in ["导航", "navbar", "菜单", "header", "侧边栏"]):
            return "navbar"
        elif any(kw in description for kw in ["弹窗", "modal", "对话框", "确认", "弹出"]):
            return "modal"
        elif any(kw in description for kw in ["卡片", "card", "面板", "区块"]):
            return "card"
        return "generic"

    def _generate_html(self, desc: str, ui_type: str) -> str:
        generators = {
            "dashboard": self._html_dashboard,
            "form": self._html_form,
            "table": self._html_table,
            "navbar": self._html_navbar,
            "card": self._html_card,
            "modal": self._html_modal,
        }
        return generators.get(ui_type, self._html_generic)(desc)

    def _html_dashboard(self, desc: str) -> str:
        title = "数据仪表盘"
        widgets = ""
        if "用户" in desc:
            widgets += '<div class="col-md-3"><div class="card text-center"><div class="card-body"><h3 class="text-primary">1,234</h3><p>用户总数</p></div></div></div>'
        if "订单" in desc:
            widgets += '<div class="col-md-3"><div class="card text-center"><div class="card-body"><h3 class="text-success">5,678</h3><p>订单数</p></div></div></div>'
        if "收入" in desc or "销售" in desc:
            widgets += '<div class="col-md-3"><div class="card text-center"><div class="card-body"><h3 class="text-warning">&#165;98,765</h3><p>收入</p></div></div></div>'
        if not widgets:
            widgets = '<div class="col-md-4"><div class="card text-center"><div class="card-body"><h3>--</h3><p>指标</p></div></div></div>' * 3

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <nav class="navbar navbar-dark bg-dark mb-4">
    <div class="container">
      <span class="navbar-brand mb-0 h1">{title}</span>
    </div>
  </nav>
  <div class="container">
    <div class="row">{widgets}</div>
    <div class="row mt-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">最近活动</div>
          <div class="card-body">
            <p class="card-text">暂无活动记录</p>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">系统状态</div>
          <div class="card-body">
            <p class="card-text">运行正常</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>'''

    def _html_form(self, desc: str) -> str:
        fields = []
        if "用户" in desc or "账号" in desc:
            fields.append({"label": "用户名", "type": "text", "ph": "请输入用户名"})
        if "密码" in desc:
            fields.append({"label": "密码", "type": "password", "ph": "请输入密码"})
        if "邮箱" in desc or "email" in desc:
            fields.append({"label": "邮箱", "type": "email", "ph": "请输入邮箱"})
        if "手机" in desc:
            fields.append({"label": "手机号", "type": "tel", "ph": "请输入手机号"})
        if not fields:
            fields = [{"label": "邮箱", "type": "email", "ph": "请输入邮箱"}]

        is_login = "登录" in desc
        field_html = ""
        for f in fields:
            field_html += f'<div class="mb-3">\n    <label class="form-label">{f["label"]}</label>\n    <input type="{f["type"]}" class="form-control" placeholder="{f["ph"]}">\n  </div>'

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{"登录" if is_login else "表单"}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center" style="min-height: 100vh;">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-5">
        <div class="card shadow">
          <div class="card-body p-5">
            <h3 class="text-center mb-4">{"欢迎登录" if is_login else "填写信息"}</h3>
            <form>
{field_html}
              <button type="submit" class="btn btn-primary w-100 mt-3">{"登录" if is_login else "提交"}</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>'''

    def _html_table(self, desc: str) -> str:
        headers = ["ID", "名称", "状态", "创建时间", "操作"]
        rows = ""
        for i in range(1, 6):
            rows += f"<tr><td>{i}</td><td>项目 {i}</td><td><span class='badge bg-success'>活跃</span></td><td>2026-05-{15-i:02d}</td><td><button class='btn btn-sm btn-outline-primary'>编辑</button></td></tr>"

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>数据表格</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <nav class="navbar navbar-dark bg-dark mb-4">
    <div class="container">
      <span class="navbar-brand mb-0 h1">数据管理</span>
    </div>
  </nav>
  <div class="container">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span class="h5 mb-0">数据列表</span>
        <button class="btn btn-primary btn-sm">新增</button>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <input type="text" class="form-control" placeholder="搜索...">
        </div>
        <table class="table table-hover">
          <thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <nav><ul class="pagination justify-content-end"><li class="page-item"><a class="page-link" href="#">上一页</a></li><li class="page-item active"><a class="page-link" href="#">1</a></li><li class="page-item"><a class="page-link" href="#">2</a></li><li class="page-item"><a class="page-link" href="#">下一页</a></li></ul></nav>
      </div>
    </div>
  </div>
</body>
</html>'''

    def _html_navbar(self, desc: str) -> str:
        dark = "暗" in desc or "dark" in desc
        theme = "dark" if dark else "light"
        bg = "navbar-dark bg-dark" if dark else "navbar-light bg-light"
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>导航栏</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <nav class="navbar navbar-expand-lg {bg}">
    <div class="container">
      <a class="navbar-brand" href="#">我的应用</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item"><a class="nav-link active" href="#">首页</a></li>
          <li class="nav-item"><a class="nav-link" href="#">功能</a></li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">更多</a>
            <ul class="dropdown-menu"><li><a class="dropdown-item" href="#">关于</a></li><li><a class="dropdown-item" href="#">帮助</a></li></ul>
          </li>
        </ul>
        <form class="d-flex"><input class="form-control me-2" type="search" placeholder="搜索"><button class="btn btn-outline-primary" type="submit">搜索</button></form>
      </div>
    </div>
  </nav>
  <div class="container mt-4"><p class="lead">导航栏示例</p></div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    def _html_card(self, desc: str) -> str:
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>卡片组件</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container py-5">
    <h2 class="mb-4">产品展示</h2>
    <div class="row">
      <div class="col-md-4">
        <div class="card h-100">
          <img src="https://via.placeholder.com/300x200" class="card-img-top" alt="产品图片">
          <div class="card-body">
            <h5 class="card-title">产品 A</h5>
            <p class="card-text">这是一个示例产品描述，包含主要特点和优势。</p>
            <button class="btn btn-primary">查看详情</button>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100">
          <img src="https://via.placeholder.com/300x200" class="card-img-top" alt="产品图片">
          <div class="card-body">
            <h5 class="card-title">产品 B</h5>
            <p class="card-text">这是一个示例产品描述，包含主要特点和优势。</p>
            <button class="btn btn-primary">查看详情</button>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100">
          <img src="https://via.placeholder.com/300x200" class="card-img-top" alt="产品图片">
          <div class="card-body">
            <h5 class="card-title">产品 C</h5>
            <p class="card-text">这是一个示例产品描述，包含主要特点和优势。</p>
            <button class="btn btn-primary">查看详情</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>'''

    def _html_modal(self, desc: str) -> str:
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>对话框</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <div class="container mt-5 text-center">
    <button class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#confirmModal">删除数据</button>
  </div>

  <div class="modal fade" id="confirmModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header bg-danger text-white">
          <h5 class="modal-title">确认删除</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <p>确定要删除这条数据吗？此操作不可撤销。</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
          <button type="button" class="btn btn-danger">确认删除</button>
        </div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    def _html_generic(self, desc: str) -> str:
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container mt-5">
    <div class="card">
      <div class="card-body text-center py-5">
        <h3>UI 组件</h3>
        <p class="text-muted">{desc}</p>
        <button class="btn btn-primary me-2">确定</button>
        <button class="btn btn-secondary">取消</button>
      </div>
    </div>
  </div>
</body>
</html>'''

    # === React 生成器 ===
    def _generate_react(self, desc: str, ui_type: str) -> str:
        if ui_type == "form":
            return '''import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log({ email, password });
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-5">
          <div className="card shadow">
            <div className="card-body p-5">
              <h3 className="text-center mb-4">欢迎登录</h3>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">邮箱</label>
                  <input
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="请输入邮箱"
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">密码</label>
                  <input
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                  />
                </div>
                <button type="submit" className="btn btn-primary w-100 mt-3">
                  登录
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}'''
        elif ui_type == "dashboard":
            return '''import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";

export default function Dashboard() {
  const stats = [
    { label: "用户总数", value: "1,234", color: "primary" },
    { label: "订单数", value: "5,678", color: "success" },
    { label: "收入", value: "\\u00a598,765", color: "warning" },
    { label: "转化率", value: "78%", color: "info" },
  ];

  return (
    <div className="bg-light min-vh-100">
      <nav className="navbar navbar-dark bg-dark mb-4">
        <div className="container">
          <span className="navbar-brand mb-0 h1">数据仪表盘</span>
        </div>
      </nav>
      <div className="container">
        <div className="row">
          {stats.map((stat, i) => (
            <div key={i} className="col-md-3">
              <div className="card text-center">
                <div className="card-body">
                  <h3 className={`text-${stat.color}`}>{stat.value}</h3>
                  <p className="text-muted mb-0">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}'''
        else:
            return '''import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";

export default function GenericUI() {
  return (
    <div className="container mt-5">
      <div className="card">
        <div className="card-body text-center py-5">
          <h3>UI 组件</h3>
          <p className="text-muted">React 组件示例</p>
          <button className="btn btn-primary me-2">确定</button>
          <button className="btn btn-secondary">取消</button>
        </div>
      </div>
    </div>
  );
}'''

    # === Vue 生成器 ===
    def _generate_vue(self, desc: str, ui_type: str) -> str:
        if ui_type == "form":
            return '''<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-5">
        <div class="card shadow">
          <div class="card-body p-5">
            <h3 class="text-center mb-4">欢迎登录</h3>
            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label class="form-label">邮箱</label>
                <input
                  type="email"
                  class="form-control"
                  v-model="email"
                  placeholder="请输入邮箱"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">密码</label>
                <input
                  type="password"
                  class="form-control"
                  v-model="password"
                  placeholder="请输入密码"
                />
              </div>
              <button type="submit" class="btn btn-primary w-100 mt-3">
                登录
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const email = ref("");
const password = ref("");

const handleSubmit = () => {
  console.log({ email: email.value, password: password.value });
};
</script>

<style scoped>
.bg-light { background-color: #f8f9fa; }
</style>'''
        elif ui_type == "dashboard":
            return '''<template>
  <div class="bg-light min-vh-100">
    <nav class="navbar navbar-dark bg-dark mb-4">
      <div class="container">
        <span class="navbar-brand mb-0 h1">数据仪表盘</span>
      </div>
    </nav>
    <div class="container">
      <div class="row">
        <div v-for="(stat, i) in stats" :key="i" class="col-md-3">
          <div class="card text-center">
            <div class="card-body">
              <h3 :class="`text-${stat.color}`">{{ stat.value }}</h3>
              <p class="text-muted mb-0">{{ stat.label }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const stats = ref([
  { label: "用户总数", value: "1,234", color: "primary" },
  { label: "订单数", value: "5,678", color: "success" },
  { label: "收入", value: "\\u00a598,765", color: "warning" },
  { label: "转化率", value: "78%", color: "info" },
]);
</script>'''
        else:
            return '''<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-body text-center py-5">
        <h3>UI 组件</h3>
        <p class="text-muted">Vue 组件示例</p>
        <button class="btn btn-primary me-2" @click="confirm">确定</button>
        <button class="btn btn-secondary" @click="cancel">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const confirm = () => console.log("confirmed");
const cancel = () => console.log("cancelled");
</script>'''

    # === Tailwind 生成器 ===
    def _generate_tailwind(self, desc: str, ui_type: str) -> str:
        if ui_type == "dashboard":
            return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>仪表盘</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
  <nav class="bg-gray-800 text-white px-6 py-4">
    <div class="flex justify-between items-center">
      <h1 class="text-xl font-bold">数据仪表盘</h1>
      <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">导出</button>
    </div>
  </nav>
  <div class="container mx-auto px-6 py-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <p class="text-gray-500">用户总数</p>
        <p class="text-3xl font-bold text-blue-600">1,234</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <p class="text-gray-500">订单数</p>
        <p class="text-3xl font-bold text-green-600">5,678</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <p class="text-gray-500">收入</p>
        <p class="text-3xl font-bold text-yellow-600">&#165;98,765</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6 text-center">
        <p class="text-gray-500">转化率</p>
        <p class="text-3xl font-bold text-purple-600">78%</p>
      </div>
    </div>
  </div>
</body>
</html>'''
        elif ui_type == "form":
            return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>登录</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
    <h2 class="text-2xl font-bold text-center mb-6">欢迎登录</h2>
    <form>
      <div class="mb-4">
        <label class="block text-gray-700 mb-2">邮箱</label>
        <input type="email" class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="请输入邮箱">
      </div>
      <div class="mb-6">
        <label class="block text-gray-700 mb-2">密码</label>
        <input type="password" class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="请输入密码">
      </div>
      <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">登录</button>
    </form>
  </div>
</body>
</html>'''
        else:
            return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow-lg p-8 text-center">
    <h3 class="text-xl font-bold mb-2">UI 组件</h3>
    <p class="text-gray-500 mb-4">{desc}</p>
    <button class="bg-blue-600 text-white px-6 py-2 rounded-lg mr-2">确定</button>
    <button class="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg">取消</button>
  </div>
</body>
</html>'''

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "status": "active",
            "history_count": len(self.history),
            "supported_types": list(set(h["ui_type"] for h in self.history)) or ["dashboard", "form", "table", "navbar", "card", "modal", "generic"],
            "supported_frameworks": ["html", "react", "vue", "tailwind"],
            "output_dir": self.output_dir,
            "files_generated": len(self.history)
        }


def run_ui_generation(description: str, framework: str = "html") -> Dict[str, Any]:
    """快捷生成函数"""
    skill = UIGeneratorSkill()
    return skill.generate(description, framework)


if __name__ == "__main__":
    print("=== UI 生成器 v2.0 测试 ===\n")

    skill = UIGeneratorSkill()

    test_cases = [
        ("数据仪表盘，显示用户数和订单数", "html"),
        ("用户登录表单", "react"),
        ("商品数据表格", "vue"),
        ("网站导航栏", "tailwind"),
        ("确认删除弹窗", "html"),
    ]

    for desc, fw in test_cases:
        result = skill.generate(desc, fw)
        print(f"[{fw}] {desc}")
        print(f"  类型: {result['ui_type']}, 文件: {result.get('filename', 'N/A')}")
        print()