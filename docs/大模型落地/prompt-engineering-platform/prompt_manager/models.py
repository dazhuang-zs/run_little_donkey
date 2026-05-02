"""
提示词核心数据模型：定义 Prompt、PromptVersion、Template 的结构。
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Template(BaseModel):
    """提示词模板：包含变量占位符的原始模板"""
    name: str = Field(description="模板名称，如 'translation_template'")
    content: str = Field(description="模板内容，使用 {{variable}} 语法")
    variables: list[str] = Field(default_factory=list, description="模板中声明的变量列表")
    description: str = Field(default="", description="模板用途说明")
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("content")
    @classmethod
    def validate_template_syntax(cls, v: str) -> str:
        """校验模板语法：确保 {{ 和 }} 成对出现"""
        # 检查花括号配对
        depth = 0
        for i, ch in enumerate(v):
            if ch == '{' and i + 1 < len(v) and v[i + 1] == '{':
                depth += 1
            elif ch == '}' and i + 1 < len(v) and v[i + 1] == '}':
                depth -= 1
                if depth < 0:
                    raise ValueError(f"位置 {i} 处有多余的闭合括号 }}")
        if depth != 0:
            raise ValueError("模板中存在未闭合的 {{ }}，请检查变量占位符")
        return v


class PromptVersion(BaseModel):
    """提示词版本：某次发布的快照"""
    version_id: str = Field(description="版本标识，如 'v1.2.3'")
    prompt_id: str = Field(description="所属提示词 ID")
    template_id: str = Field(description="使用的模板 ID")
    template_content: str = Field(description="该版本冻结的模板内容（避免模板变更影响历史版本）")
    llm_config: dict = Field(default_factory=dict, description="模型参数配置，如 {'model': 'gpt-4', 'temperature': 0.3}")
    commit_message: str = Field(default="", description="版本提交说明")
    author: str = Field(default="unknown", description="修改者标识")
    created_at: datetime = Field(default_factory=datetime.now)
    parent_version: Optional[str] = Field(default=None, description="父版本 ID，用于追溯版本历史")

    @property
    def semver_tuple(self) -> tuple:
        """将版本号解析为可比较的元组，如 'v1.2.3' -> (1, 2, 3)"""
        parts = self.version_id.lstrip("v").split(".")
        try:
            return tuple(int(p) for p in parts)
        except ValueError:
            return (0, 0, 0)


class Prompt(BaseModel):
    """提示词实体：包含完整生命周期信息"""
    prompt_id: str = Field(description="提示词唯一标识")
    name: str = Field(description="提示词名称，如 'customer_support_v2'")
    description: str = Field(default="", description="功能描述")
    current_version: str = Field(default="v0.0.0", description="当前线上版本号")
    tags: list[str] = Field(default_factory=list, description="标签，用于分类和搜索")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="draft", description="状态: draft / staging / production / deprecated")
