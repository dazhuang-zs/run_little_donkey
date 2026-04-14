"""AI 意图解析服务"""
from typing import Optional
import json
import httpx
from app.models.trip import TripIntent
from app.core.exceptions import AIParseError
from app.core.config import get_settings

settings = get_settings()


class AIParserService:
    """AI 意图解析"""

    SYSTEM_PROMPT = """你是一个旅行规划助手。

用户会输入旅行需求，请提取以下信息并以JSON格式返回：
- city: 城市名（必填）
- days: 天数（必填，数字）
- attractions: 景点列表（必填，数组）
- hotel_area: 住宿区域偏好（可选）
- budget_per_night: 每晚预算（可选，数字，单位元）
- transport_mode: 交通偏好（可选：driving/walking/transit/mixed）

只返回JSON，不要其他内容。"""


    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL

    async def parse(self, user_input: str) -> TripIntent:
        """解析用户输入"""
        if not self.api_key:
            # 简单规则解析（无API时备用）
            return self._simple_parse(user_input)

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.3,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            # 提取 JSON
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            info = json.loads(json_str)
            return TripIntent(**info)

        except Exception as e:
            raise AIParseError(f"解析失败: {str(e)}")

    def _simple_parse(self, user_input: str) -> TripIntent:
        """简单规则解析（无API时用）"""
        import re
        # 提取城市（简化版）
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "南京", "苏州"]
        city = None
        for c in cities:
            if c in user_input:
                city = c
                break

        # 提取天数
        day_match = re.search(r"(\d+)天", user_input)
        days = int(day_match.group(1)) if day_match else 3

        # 简化处理
        attractions = []
        parts = user_input.replace(city or "", "").split("，")
        for p in parts:
            p = p.strip()
            if p and len(p) > 1:
                attractions.append(p[:20])

        return TripIntent(
            city=city or "北京",
            days=days,
            attractions=attractions or ["故宫", "天安门"],
        )
