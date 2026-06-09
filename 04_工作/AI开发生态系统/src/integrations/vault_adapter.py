"""
HashiCorp Vault 集成适配器
将 vault (https://github.com/hashicorp/vault) 作为秘钥管理平台集成
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import os


@dataclass
class Secret:
    """秘钥"""
    key: str
    value: str
    version: int
    metadata: Dict[str, Any]


class VaultAdapter:
    """
    Vault 适配器 - 秘钥管理, 加密即服务 (35k stars)

    功能:
    - 秘钥存储和轮换
    - 加密即服务
    - PKI 证书管理
    - AWS/GCP/Azure 云集成
    """

    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN", "")
        self.client = None
        self._connected = False
        self._connect()

    def _connect(self) -> bool:
        """连接 Vault"""
        try:
            import hvac
            self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            self._connected = self.client.is_authenticated()
            return self._connected
        except ImportError:
            print("警告: hvac 未安装，使用模拟模式")
            self._connected = False
            return False
        except Exception as e:
            print(f"Vault 连接失败: {e}")
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    def read_secret(self, path: str, key: str) -> Optional[str]:
        """读取秘钥"""
        if not self.client:
            return self._mock_read(path, key)

        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            if secret and secret.data:
                return secret.data.get("data", {}).get(key)
        except Exception as e:
            print(f"读取秘钥失败: {e}")
        return None

    def write_secret(self, path: str, key: str, value: str) -> bool:
        """写入秘钥"""
        if not self.client:
            return self._mock_write(path, key, value)

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret={key: value}
            )
            return True
        except Exception as e:
            print(f"写入秘钥失败: {e}")
            return False

    def delete_secret(self, path: str) -> bool:
        """删除秘钥"""
        if not self.client:
            return False

        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            return True
        except Exception:
            return False

    def list_secrets(self, path: str) -> List[str]:
        """列出路径下的秘钥"""
        if not self.client:
            return []

        try:
            secrets = self.client.secrets.kv.v2.listSecrets(path=path)
            return secrets.data.get("keys", [])
        except Exception:
            return []

    def rotate_secret(self, path: str, key: str) -> bool:
        """轮换秘钥"""
        # 读取当前值
        current = self.read_secret(path, key)
        if current is None:
            return False

        # 生成新值（实际应该调用秘钥生成API）
        import secrets
        new_value = secrets.token_urlsafe(32)

        # 写入新值
        return self.write_secret(path, key, new_value)

    def get_secret_metadata(self, path: str) -> Dict[str, Any]:
        """获取秘钥元数据"""
        if not self.client:
            return {}

        try:
            metadata = self.client.secrets.kv.v2.read_secret_metadata(path=path)
            return {
                "versions": metadata.data.get("versions", {}),
                "current_version": metadata.data.get("current_version", 1)
            }
        except Exception:
            return {}

    # 模拟模式（Vault 不可用时）
    def _mock_read(self, path: str, key: str) -> Optional[str]:
        """模拟读取"""
        print(f"[模拟] 读取: {path}/{key}")
        return f"mock_value_for_{key}"

    def _mock_write(self, path: str, key: str, value: str) -> bool:
        """模拟写入"""
        print(f"[模拟] 写入: {path}/{key} = {value[:8]}...")
        return True


class SecretManager:
    """秘钥管理器 - 统一接口"""

    def __init__(self, use_vault: bool = True):
        self.use_vault = use_vault
        if use_vault:
            self.vault = VaultAdapter()
            if not self.vault.is_connected():
                print("警告: Vault 不可用，切换到环境变量模式")
                self.use_vault = False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取秘钥"""
        if self.use_vault:
            return self.vault.read_secret("hermes", key) or default
        return os.getenv(key, default)

    def set(self, key: str, value: str, path: str = "hermes") -> bool:
        """设置秘钥"""
        if self.use_vault:
            return self.vault.write_secret(path, key, value)
        os.environ[key] = value
        return True

    def rotate(self, key: str) -> bool:
        """轮换秘钥"""
        if self.use_vault:
            return self.vault.rotate_secret("hermes", key)
        return False


if __name__ == "__main__":
    print("=== Vault 集成适配器 ===\n")

    manager = SecretManager()

    print(f"Vault 连接状态: {'已连接' if manager.vault.is_connected() else '未连接 (使用环境变量)' if not manager.use_vault else '模拟模式'}")

    # 测试
    manager.set("test_key", "test_value")
    value = manager.get("test_key")
    print(f"测试读取: {value}")

    print("\n✓ Vault 适配器就绪")
