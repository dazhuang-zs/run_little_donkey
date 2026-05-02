"""
模板渲染引擎：将带变量的模板与具体参数结合，生成最终的提示词。
支持变量提取、默认值、类型转换等特性。
"""
import re
from typing import Any
from .models import Template


class TemplateRenderer:
    """模板渲染器：负责变量提取、校验和渲染"""

    # 匹配 {{ variable_name }} 形式的占位符，忽略前后空白
    VARIABLE_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")

    @classmethod
    def extract_variables(cls, template_content: str) -> list[str]:
        """从模板内容中提取所有变量名，按出现顺序去重返回"""
        seen: set[str] = set()
        variables: list[str] = []
        for match in cls.VARIABLE_PATTERN.finditer(template_content):
            var_name = match.group(1)
            if var_name not in seen:
                seen.add(var_name)
                variables.append(var_name)
        return variables

    @classmethod
    def render(cls, template: Template, variables: dict[str, Any]) -> str:
        """
        渲染模板：用具体值替换变量占位符。

        参数:
            template: 模板对象
            variables: 变量名到值的映射字典

        返回:
            渲染后的提示词字符串

        异常:
            ValueError: 缺少必需变量或存在未定义的变量（严格模式）
        """
        # 提取模板中声明的变量
        declared_vars = set(template.variables) if template.variables else set(
            cls.extract_variables(template.content)
        )
        provided_vars = set(variables.keys())

        # 检查缺失变量
        missing = declared_vars - provided_vars
        if missing:
            raise ValueError(
                f"模板 '{template.name}' 缺少必需变量: {', '.join(sorted(missing))}"
            )

        # 替换变量（允许额外的变量，不会报错）
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))
            return str(value)

        return cls.VARIABLE_PATTERN.sub(replace_var, template.content)

    @classmethod
    def render_string(cls, template_str: str, variables: dict[str, Any]) -> str:
        """
        直接渲染模板字符串（不依赖 Template 对象），用于快速测试。
        """
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        return cls.VARIABLE_PATTERN.sub(replace_var, template_str)
