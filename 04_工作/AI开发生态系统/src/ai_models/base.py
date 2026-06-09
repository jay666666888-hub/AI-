#!/usr/bin/env python3
"""
Model Provider Base Class
"""

import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class ProviderType(Enum):
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class ModelResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0})
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ModelProvider(ABC):
    """AI模型提供者基类"""

    def __init__(self, api_key: str, base_url: str = None, default_model: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self._client = None
        self._init_client()

    @abstractmethod
    def _init_client(self):
        """初始化客户端"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> ModelResponse:
        """发送对话请求"""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """列出可用模型"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.list_models()
            return True
        except Exception:
            return False
