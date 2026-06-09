#!/usr/bin/env python3
"""
统一配置层 - Pydantic Settings 管理
所有配置集中管理，支持 .env 文件和环境变量覆盖
"""

import os
from typing import Optional, List
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM 配置"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    provider: str = Field(default="minimax")
    model: str = Field(default="minimax/DeepThinker")
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)


class QdrantSettings(BaseSettings):
    """Qdrant 向量数据库配置"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=6333)
    collection_name: str = Field(default="ai_ecosystem_memory")
    vector_size: int = Field(default=768)
    distance: str = Field(default="cosine")


class VaultSettings(BaseSettings):
    """Vault 安全配置"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    url: str = Field(default="http://localhost:8200")
    token: Optional[str] = Field(default=None)
    mock_mode: bool = Field(default=True)


class DockerSettings(BaseSettings):
    """Docker 容器配置"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="unix:///var/run/docker.sock")


class Settings(BaseSettings):
    """全局配置 - 统一入口"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = Field(default="AI 开发生态系统")
    version: str = Field(default="4.0")

    llm: LLMSettings = Field(default_factory=LLMSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    docker: DockerSettings = Field(default_factory=DockerSettings)


_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings
