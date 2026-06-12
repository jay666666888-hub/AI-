"""
结构化日志配置
"""
import logging
import json
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # 添加 extra 字段
        if hasattr(record, 'user_id'):
            log_obj["user_id"] = record.user_id
        if hasattr(record, 'action'):
            log_obj["action"] = record.action
        if hasattr(record, 'entity_type'):
            log_obj["entity_type"] = record.entity_type
        if hasattr(record, 'entity_id'):
            log_obj["entity_id"] = str(record.entity_id) if record.entity_id else None
        return json.dumps(log_obj, ensure_ascii=False)

def setup_logging(log_file: str = "/var/log/ai-brain.log"):
    """配置日志"""
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建 logger
    logger = logging.getLogger("ai_brain")
    logger.setLevel(logging.INFO)

    # 文件处理器 - JSON 格式
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())

    # 控制台处理器 - 简单格式
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 全局 logger
logger = setup_logging()