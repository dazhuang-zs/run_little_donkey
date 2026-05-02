"""Configuration management."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LLMConfig:
    """大模型API配置"""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.1  # 低温度=更确定性输出
    request_timeout: int = 120


@dataclass
class ReviewConfig:
    """审阅配置"""
    dimensions: list[str] = field(
        default_factory=lambda: ["security", "performance", "style", "logic"]
    )
    max_tokens_per_chunk: int = 4000
    concurrency: int = 3
    min_confidence: float = 0.3  # 低于此置信度的发现将被过滤
    output_format: str = "rich"   # rich / json / both
    output_file: Optional[str] = None


@dataclass
class AppConfig:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)
    debug: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        """加载配置，优先级：环境变量 > 配置文件 > 默认值"""
        cfg = cls()

        # 加载YAML配置文件
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                # 合并YAML配置到默认值（略，保持简洁）
                if "llm" in data:
                    for k, v in data["llm"].items():
                        if hasattr(cfg.llm, k) and v is not None:
                            setattr(cfg.llm, k, v)
                if "review" in data:
                    for k, v in data["review"].items():
                        if hasattr(cfg.review, k) and v is not None:
                            setattr(cfg.review, k, v)

        # 环境变量覆盖（最高优先级）
        cfg.llm.api_key = os.getenv("LLM_API_KEY", cfg.llm.api_key)
        cfg.llm.base_url = os.getenv("LLM_BASE_URL", cfg.llm.base_url)
        cfg.llm.model = os.getenv("LLM_MODEL", cfg.llm.model)

        dims_env = os.getenv("REVIEW_DIMENSIONS")
        if dims_env:
            cfg.review.dimensions = [d.strip() for d in dims_env.split(",")]

        tokens_env = os.getenv("MAX_TOKENS_PER_CHUNK")
        if tokens_env:
            cfg.review.max_tokens_per_chunk = int(tokens_env)

        concurrency_env = os.getenv("CONCURRENCY")
        if concurrency_env:
            cfg.review.concurrency = int(concurrency_env)

        return cfg
