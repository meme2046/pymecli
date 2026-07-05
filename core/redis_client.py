import json
import os
from typing import Any, Optional

import redis


class RedisClient:
    def __init__(
        self,
        host=os.getenv("REDIS_HOST", "192.168.123.7"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    ):
        """
        初始化Redis客户端
        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param db: 数据库编号
        :param password: 密码（如果需要）
        :param decode_responses: 是否自动解码响应（将字节转换为字符串）
        """

        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # 测试连接
        self.client.ping()

    def get_value(self, key: str) -> Optional[Any]:
        """
        根据key获取值
        :param key: Redis中的键名
        :return: 键对应的值, 如果键不存在则返回None
        """
        if not self.client:
            return None

        return self.client.get(key)

    def get_all_keys(self, pattern: str = "*"):
        """
        获取所有匹配的键
        :param pattern: 键的匹配模式，默认为"*"匹配所有键
        :return: 匹配的键列表
        """
        if not self.client:
            return []

        return self.client.keys(pattern)

    def set_value(self, key: str, value: Any, expire: int | None = None):
        """
        设置键值对
        :param key: 键名
        :param value: 值
        :param expire: 过期时间（秒），如果提供则在指定时间后过期
        :return: 设置成功返回True, 否则返回False
        """
        if not self.client:
            return False

        # 如果值是字典或列表，转换为JSON字符串存储
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        result = self.client.set(key, value)
        if expire:
            self.client.expire(key, expire)
        return result

    def get_hash_value(self, name: str, key: str):
        """
        获取哈希类型数据中的值
        :param name: 哈希表名称
        :param key: 哈希表中的键
        :return: 键对应的值
        """
        if not self.client:
            return None

        return self.client.hget(name, key)

    def get_list(self, key: str):
        """
        获取列表类型数据
        :param key: 列表键名
        :return: 列表内容
        """
        if not self.client:
            return []

        return self.client.lrange(key, 0, -1)

    def close(self):
        """
        关闭Redis连接
        """
        if self.client:
            self.client.close()


# 使用示例
if __name__ == "__main__":
    # 创建Redis客户端实例
    client = RedisClient()
    # 示例1: 获取普通键值
    key = "baidu.finance.getbanner"
    value = client.get_value(key)
    print(f"键 '{key}' 的值为: {value}")

    # 示例2: 获取所有键
    all_keys = client.get_all_keys()
    print(f"所有键: {all_keys}")
    print(f"所有键: {type(all_keys)}")

    # 示例3: 设置键值
    client.set_value("test_key", {"name": "张三", "age": 30}, expire=3600)

    # 示例4: 获取哈希值
    hash_value = client.get_hash_value("my_hash", "field1")
    print(f"哈希值: {hash_value}")

    # 示例5: 获取列表值
    list_value = client.get_list("my_list")
    print(f"列表值: {list_value}")

    # 关闭连接
    client.close()
