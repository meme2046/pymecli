import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

import etcd3

DEFAULT_ETCD_URL = "http://localhost:2379"


def _parse_etcd_url(url: str) -> tuple[str, int]:
    """
    解析 ETCD_URL 为 (host, port)。

    支持格式:
        http://localhost:2379
        https://127.0.0.1:2379
        localhost:2379
        127.0.0.1
    """
    if "://" not in url:
        url = f"http://{url}"
    parts = urlsplit(url)
    host = parts.hostname or "localhost"
    port = parts.port or 2379
    return host, port


def get_etcd_client(env_path: str = ".env") -> "etcd3.Etcd3Client":
    """
    创建 etcd v3 客户端。

    从环境变量 ETCD_URL 读取连接地址，默认 http://localhost:2379。
    """
    load_dotenv(env_path)
    etcd_url = os.getenv("ETCD_URL", DEFAULT_ETCD_URL)
    host, port = _parse_etcd_url(etcd_url)

    return etcd3.client(host=host, port=port)
