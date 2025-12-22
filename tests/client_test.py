#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
斗地主API客户端示例
展示了如何调用OCR和Douzero两个模块的API
"""

import base64
from typing import List, Optional

import requests


class DoudizhuClient:
    """斗地主API客户端"""

    def __init__(self, base_url: str = "http://localhost:443"):
        """
        初始化客户端

        Args:
            base_url: API服务的基础URL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def ocr_find_cards(
        self,
        image_path: str,
        region: Optional[List[int]] = None,
        is_align_y: bool = False,
        is_preprocess: bool = False,
    ) -> dict:
        """
        调用OCR API识别图片中的扑克牌

        Args:
            image_path: 图片路径
            region: 识别区域 [x, y, w, h]
            is_align_y: 是否对齐Y轴
            is_preprocess: 是否预处理图片

        Returns:
            识别结果
        """
        # 读取并编码图片
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        # 构造请求数据
        payload = {
            "img": img_base64,
            "region": region,
            "is_align_y": is_align_y,
            "is_preprocess": is_preprocess,
        }

        # 发送请求
        response = self.session.post(f"{self.base_url}/api/v1/ocr/cards", json=payload)

        return response.json()

    def ocr_find_one(
        self,
        image_path: str,
        target: str,
        region: Optional[List[int]] = None,
        is_preprocess: bool = False,
    ) -> dict:
        """
        调用OCR API识别图片中的指定文本

        Args:
            image_path: 图片路径
            target: 目标文本
            region: 识别区域 [x, y, w, h]
            is_preprocess: 是否预处理图片

        Returns:
            识别结果
        """
        # 读取并编码图片
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        # 构造请求数据
        payload = {
            "img": img_base64,
            "target": target,
            "region": region,
            "is_preprocess": is_preprocess,
        }

        # 发送请求
        response = self.session.post(f"{self.base_url}/api/v1/ocr/one", json=payload)

        return response.json()

    def ocr_find_n(
        self,
        image_path: str,
        target_list: List[str],
        region: Optional[List[int]] = None,
        is_preprocess: bool = False,
    ) -> dict:
        """
        调用OCR API识别图片中的多个指定文本

        Args:
            image_path: 图片路径
            target_list: 目标文本列表
            region: 识别区域 [x, y, w, h]
            is_preprocess: 是否预处理图片

        Returns:
            识别结果
        """
        # 读取并编码图片
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        # 构造请求数据
        payload = {
            "img": img_base64,
            "target_list": target_list,
            "region": region,
            "is_preprocess": is_preprocess,
        }

        # 发送请求
        response = self.session.post(f"{self.base_url}/api/v1/ocr/n", json=payload)

        return response.json()

    def douzero_bid_score(self, cards: str) -> dict:
        """
        调用Douzero API计算叫地主分数

        Args:
            cards: 手牌字符串，长度必须为17

        Returns:
            叫分结果
        """
        # 发送请求
        response = self.session.get(
            f"{self.base_url}/api/v1/douzero/bid", params={"cards": cards}
        )

        return response.json()

    def douzero_pre_game_score(
        self, cards: str, three: str, position_code: str
    ) -> dict:
        """
        调用Douzero API计算游戏前评估分数

        Args:
            cards: 手牌字符串，长度17或20
            three: 底牌三张
            position_code: 位置代码 ("0": 地主上家, "1": 地主, "2": 地主下家)

        Returns:
            评估结果
        """
        # 发送请求
        response = self.session.get(
            f"{self.base_url}/api/v1/douzero/pre",
            params={"cards": cards, "three": three, "position_code": position_code},
        )

        return response.json()

    def douzero_play(
        self,
        cards: str,
        three: str,
        position_code: str,
        other_cards: str = "",
        played_list: List[str] | None = None,
    ) -> dict:
        """
        调用Douzero API获取出牌建议

        Args:
            cards: 开局前的手牌,17或20张
            other_cards: 开局前其他玩家手牌,34张或37张
            played_list: 已经打出的牌列表
            three: 三张底牌
            position_code: 位置代码 ("0": 地主在右边, "1": 我是地主, "2": 地主在左边)

        Returns:
            出牌建议
        """
        if played_list is None:
            played_list = []

        # 构造请求数据
        payload = {
            "cards": cards,
            "other_cards": other_cards,
            "played_list": played_list,
            "three": three,
            "position_code": position_code,
        }

        # 发送请求
        response = self.session.post(
            f"{self.base_url}/api/v1/douzero/play", json=payload
        )

        return response.json()


# 使用示例
if __name__ == "__main__":
    # 创建客户端实例
    client = DoudizhuClient("http://localhost:443")

    # 示例：调用OCR API识别卡片
    # 注意：需要有实际的图片文件才能运行以下代码
    # result = client.ocr_find_cards("path/to/your/image.jpg")
    # print("OCR Cards Result:", json.dumps(result, indent=2, ensure_ascii=False))

    # 示例：调用叫地主评分API
    # result = client.douzero_bid_score("3334445556789TJQKA")
    # print("Bid Score Result:", json.dumps(result, indent=2, ensure_ascii=False))

    print("斗地主API客户端示例已创建")
    print("请根据实际情况修改base_url并取消注释相应代码段以测试API调用")
