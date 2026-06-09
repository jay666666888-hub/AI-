"""
Secret Manager - 秘钥管理器
支持 HashiCorp Vault 集成，环境变量管理
"""

from typing import Dict, Any, Optional, List
import os
from dataclasses import dataclass


@dataclass
class Secret:
    key: str
    value: str
    source: str  # env, vault, file
    last_rotated: Optional[str] = None


class SecretManager:
    """秘钥管理器 - 支持 Vault 和环境变量"""

    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.secrets: Dict[str, Secret] = {}
        self._vault_client = None

        if self.vault_addr and self.vault_token:
            self._init_vault()

    def _init_vault(self) -> bool:
        """初始化 Vault 客户端"""
        try:
            import hvac
            self._vault_client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            return self._vault_client.is_authenticated()
        except ImportError:
            print("警告: hvac 未安装，Vault 集成不可用")
            return False
        except Exception as e:
            print(f"Vault 连接失败: {e}")
            return False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取秘钥"""
        # 优先从缓存获取
        if key in self.secrets:
            return self.secrets[key].value

        # 从环境变量获取
        value = os.getenv(key)
        if value:
            self.secrets[key] = Secret(key=key, value=value, source="env")
            return value

        # 从 Vault 获取
        if self._vault_client:
            try:
                secret = self._vault_client.secrets.kv.v2.read_secret_version(path=key)
                if secret and secret.data:
                    value = secret.data.get("data", {}).get("value")
                    if value:
                        self.secrets[key] = Secret(key=key, value=value, source="vault")
                        return value
            except Exception:
                pass

        return default

    def set(self, key: str, value: str, source: str = "env") -> None:
        """设置秘钥"""
        self.secrets[key] = Secret(key=key, value=value, source=source)
        if source == "env":
            os.environ[key] = value

    def list_keys(self) -> List[str]:
        """列出所有秘钥名"""
        return list(self.secrets.keys())

    def rotate(self, key: str) -> bool:
        """轮换秘钥（需要 Vault）"""
        if not self._vault_client:
            print("错误: 需要 Vault 连接才能轮换秘钥")
            return False

        try:
            self._vault_client.secrets.kv.v2.rotate_key(key)
            return True
        except Exception as e:
            print(f"轮换失败: {e}")
            return False

    def load_from_env_file(self, file_path: str) -> int:
        """从 .env 文件加载秘钥"""
        from dotenv import load_dotenv
        load_dotenv(file_path)

        count = 0
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.set(key, value, source="env")
                    count += 1

        return count


if __name__ == "__main__":
    manager = SecretManager()

    # 示例：从 .env 加载
    count = manager.load_from_env_file(".env")
    print(f"加载了 {count} 个秘钥")
    print(f"可用秘钥: {manager.list_keys()}")
