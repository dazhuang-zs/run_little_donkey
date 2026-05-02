"""LLM API client wrapper with retry and error handling."""

import asyncio
import json
import time
from typing import Optional

from openai import AsyncOpenAI


class LLMClient:
    """封装OpenAI兼容API客户端，支持重试、超时、token追踪"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        timeout: int = 120,
    ):
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        # token统计
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.api_call_count = 0
        self.api_error_count = 0

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(self, messages: list[dict]) -> dict:
        """调用LLM chat completion，自动重试"""
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    response_format={"type": "json_object"},
                )
                self.api_call_count += 1

                # 统计token消耗
                usage = response.usage
                if usage:
                    self.total_prompt_tokens += usage.prompt_tokens
                    self.total_completion_tokens += usage.completion_tokens
                    # 估算成本（GPT-4o近似价格）
                    self.total_cost += (
                        usage.prompt_tokens * 2.5 / 1_000_000 +
                        usage.completion_tokens * 10 / 1_000_000
                    )

                return {
                    "content": response.choices[0].message.content or "",
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens if usage else 0,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                        "total_tokens": usage.total_tokens if usage else 0,
                    },
                }

            except Exception as e:
                last_error = e
                self.api_error_count += 1
                if attempt < max_retries - 1:
                    # 指数退避：1s, 2s, 4s
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                continue

        return {
            "content": json.dumps({"findings": []}),
            "error": str(last_error),
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def get_usage_summary(self) -> dict:
        """获取使用统计"""
        return {
            "model": self._model,
            "api_calls": self.api_call_count,
            "api_errors": self.api_error_count,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "estimated_cost_usd": round(self.total_cost, 4),
        }
