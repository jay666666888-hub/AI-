# AI 开发生态系统 - 运行手册

## 环境要求

- Python 3.10+
- Docker (用于 Qdrant、Grafana 等服务)
- 5GB+ 磁盘空间

---

## 快速启动

### 1. 一键初始化

```bash
# 克隆项目后，运行初始化脚本
python init_env.py
```

### 2. 启动依赖服务

```bash
# 启动 Docker 服务
docker-compose up -d

# 验证服务
docker-compose ps
```

### 3. 健康检查

```bash
# Linux/WSL
./venv/bin/python src/ecosystem_doctor.py

# Windows
.\venv\Scripts\python.exe src\ecosystem_doctor.py
```

---

## Windows 本地运行

```powershell
# 1. 进入项目目录
cd E:\黑曜石\04_工作\AI开发生态系统

# 2. 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动依赖服务
docker-compose up -d

# 5. 运行健康检查
python src/ecosystem_doctor.py

# 6. 运行主程序
python src/ecosystem.py
```

---

## WSL/Linux 运行

```bash
# 1. 进入项目目录
cd /mnt/e/黑曜石/04_工作/AI开发生态系统

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动依赖服务
docker-compose up -d

# 5. 运行健康检查
python src/ecosystem_doctor.py

# 6. 运行主程序
python src/ecosystem.py
```

---

## 故障排查

### Qdrant 连接失败

```bash
# 检查容器是否运行
docker-compose ps qdrant

# 查看日志
docker-compose logs qdrant

# 重启服务
docker-compose restart qdrant
```

### Python 模块导入失败

```bash
# 确认虚拟环境已激活
which python  # 应该指向 venv/bin/python 或 venv/Scripts/python.exe

# 重新安装依赖
pip install -r requirements.txt
```

### Vault Token 问题

Vault 在 `.env` 中配置，如未设置会使用 mock 模式（不真实存储密钥）。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `ecosystem.py` | 主入口 |
| `ecosystem_doctor.py` | 健康检查 |
| `ecosystem_closed_loop_demo.py` | 最小闭环演示 |
| `ecosystem_orchestrator.py` | 编排器 |
| `docker-compose.yml` | 服务依赖 |
| `requirements.txt` | Python 依赖 |
| `config/settings.py` | 统一配置层 |

---

**最后更新**: 2026-05-14
