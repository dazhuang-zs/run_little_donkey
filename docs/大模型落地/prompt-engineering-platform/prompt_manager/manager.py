"""
PromptManager：面向业务的高层 API，封装了模板管理、提示词 CRUD 和版本控制。
"""
import uuid
from datetime import datetime
from typing import Optional, Any
from .models import Prompt, PromptVersion, Template
from .repository import PromptRepository
from .template import TemplateRenderer


class PromptManager:
    """提示词管理器：协调模板、提示词和版本的生命周期管理"""

    def __init__(self, db_path: str = "prompt_engine.db"):
        self.repo = PromptRepository(db_path)

    # ========== 模板管理 ==========

    def create_template(
        self, name: str, content: str, description: str = ""
    ) -> Template:
        """创建新模板：自动提取变量列表并保存"""
        variables = TemplateRenderer.extract_variables(content)
        template = Template(
            name=name,
            content=content,
            variables=variables,
            description=description,
        )
        self.repo.save_template(template)
        return template

    def get_template(self, name: str) -> Optional[Template]:
        return self.repo.get_template(name)

    def list_templates(self) -> list[Template]:
        return self.repo.list_templates()

    # ========== 提示词管理 ==========

    def create_prompt(
        self, name: str, description: str = "", tags: list[str] | None = None
    ) -> Prompt:
        """创建新的提示词，自动生成唯一 ID"""
        prompt = Prompt(
            prompt_id=f"prompt_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            tags=tags or [],
        )
        self.repo.save_prompt(prompt)
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        return self.repo.get_prompt(prompt_id)

    def list_prompts(self, status: Optional[str] = None) -> list[Prompt]:
        return self.repo.list_prompts(status)

    # ========== 版本管理 ==========

    def _next_version(self, prompt_id: str, bump: str = "patch") -> str:
        """基于语义化版本计算下一个版本号"""
        prompt = self.repo.get_prompt(prompt_id)
        if not prompt or prompt.current_version == "v0.0.0":
            return "v0.1.0"

        try:
            major, minor, patch = (int(x) for x in prompt.current_version.lstrip("v").split("."))
        except ValueError:
            return "v0.1.0"

        if bump == "major":
            return f"v{major + 1}.0.0"
        elif bump == "minor":
            return f"v{major}.{minor + 1}.0"
        else:  # patch
            return f"v{major}.{minor}.{patch + 1}"

    def create_version(
        self,
        prompt_id: str,
        template_id: str,
        llm_config: dict[str, Any] | None = None,
        commit_message: str = "",
        author: str = "unknown",
        bump: str = "patch",
    ) -> PromptVersion:
        """
        创建新版本：冻结当前模板内容，保存模型参数，创建版本快照。
        这是提示词工程化的核心操作 —— 版本即快照。
        """
        prompt = self.repo.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"提示词 {prompt_id} 不存在")

        template = self.repo.get_template(template_id)
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        new_version_id = self._next_version(prompt_id, bump)

        # 获取父版本
        parent = prompt.current_version if prompt.current_version != "v0.0.0" else None

        version = PromptVersion(
            version_id=new_version_id,
            prompt_id=prompt_id,
            template_id=template_id,
            template_content=template.content,  # 冻结模板内容！
            llm_config=llm_config or {"model": "gpt-4", "temperature": 0.3},
            commit_message=commit_message,
            author=author,
            parent_version=parent,
        )

        # 保存版本并更新提示词的当前版本
        self.repo.save_version(version)
        prompt.current_version = new_version_id
        prompt.updated_at = datetime.now()
        self.repo.save_prompt(prompt)

        return version

    def get_version(
        self, prompt_id: str, version_id: str
    ) -> Optional[PromptVersion]:
        return self.repo.get_version(prompt_id, version_id)

    def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        return self.repo.list_versions(prompt_id)

    def get_version_history(self, prompt_id: str) -> list[dict]:
        return self.repo.get_version_history(prompt_id)

    def rollback(self, prompt_id: str, target_version: str) -> PromptVersion:
        """
        回滚到指定版本：创建一个新版本，但内容来自历史版本。
        不删除历史，只创建"回滚快照"——这是 Git 式管理的核心原则。
        """
        target = self.repo.get_version(prompt_id, target_version)
        if not target:
            raise ValueError(f"目标版本 {target_version} 不存在")

        prompt = self.repo.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"提示词 {prompt_id} 不存在")

        new_version_id = self._next_version(prompt_id, "patch")

        version = PromptVersion(
            version_id=new_version_id,
            prompt_id=prompt_id,
            template_id=target.template_id,
            template_content=target.template_content,
            llm_config=target.llm_config.copy(),
            commit_message=f"rollback to {target_version}",
            author="system",
            parent_version=prompt.current_version,
        )

        self.repo.save_version(version)
        prompt.current_version = new_version_id
        prompt.updated_at = datetime.now()
        self.repo.save_prompt(prompt)

        return version
