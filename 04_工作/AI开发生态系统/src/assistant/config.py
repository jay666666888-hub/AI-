# AI 开发生态系统 - Assistant 配置
"""
配置文件定义 AI 助手的默认行为
"""

from typing import Optional
from pydantic import BaseModel, Field


class AssistantConfig(BaseModel):
    """AI 助手配置"""
    
    # 角色配置
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="使用的 LLM 模型"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度"
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="最大 token 数"
    )
    
    # 记忆配置
    memory_enabled: bool = Field(
        default=True,
        description="是否启用记忆功能"
    )
    memory_top_k: int = Field(
        default=5,
        gt=0,
        description="记忆检索返回数量"
    )
    
    # 工具配置
    tools_enabled: bool = Field(
        default=True,
        description="是否启用工具调用"
    )
    
    # 安全配置
    security_scan_enabled: bool = Field(
        default=True,
        description="是否启用安全扫描"
    )
    
    # 执行配置
    verbose: bool = Field(
        default=False,
        description="详细输出模式"
    )
    
    class Config:
        frozen = False
        
    def to_dict(self) -> dict:
        return self.model_dump()
