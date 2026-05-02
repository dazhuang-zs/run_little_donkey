"""
持久化层：使用 SQLite 存储提示词、版本和模板。
提供 CRUD 操作和版本历史追溯能力。
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional
from .models import Prompt, PromptVersion, Template


class PromptRepository:
    """提示词仓库：封装 SQLite 存储逻辑"""

    def __init__(self, db_path: str = "prompt_engine.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接（每次调用创建新连接，避免线程安全问题）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS templates (
                    name TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    variables TEXT NOT NULL DEFAULT '[]',
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS prompts (
                    prompt_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    current_version TEXT DEFAULT 'v0.0.0',
                    tags TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT DEFAULT 'draft'
                );
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    version_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    template_content TEXT NOT NULL,
                    llm_config TEXT DEFAULT '{}',
                    commit_message TEXT DEFAULT '',
                    author TEXT DEFAULT 'unknown',
                    created_at TEXT NOT NULL,
                    parent_version TEXT,
                    PRIMARY KEY (version_id, prompt_id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts(prompt_id)
                );
                CREATE INDEX IF NOT EXISTS idx_versions_prompt
                    ON prompt_versions(prompt_id, created_at DESC);
            """)

    # ---- Template CRUD ----

    def save_template(self, template: Template) -> None:
        """保存或更新模板"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO templates
                   (name, content, variables, description, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (template.name, template.content,
                 json.dumps(template.variables),
                 template.description,
                 template.created_at.isoformat()),
            )

    def get_template(self, name: str) -> Optional[Template]:
        """按名称获取模板"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM templates WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return Template(
            name=row["name"],
            content=row["content"],
            variables=json.loads(row["variables"]),
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_templates(self) -> list[Template]:
        """列出所有模板"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM templates ORDER BY created_at DESC"
            ).fetchall()
        return [
            Template(
                name=r["name"],
                content=r["content"],
                variables=json.loads(r["variables"]),
                description=r["description"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # ---- Prompt CRUD ----

    def save_prompt(self, prompt: Prompt) -> None:
        """保存或更新提示词"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO prompts
                   (prompt_id, name, description, current_version,
                    tags, created_at, updated_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (prompt.prompt_id, prompt.name, prompt.description,
                 prompt.current_version, json.dumps(prompt.tags),
                 prompt.created_at.isoformat(),
                 prompt.updated_at.isoformat(),
                 prompt.status),
            )

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """按 ID 获取提示词"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM prompts WHERE prompt_id = ?", (prompt_id,)
            ).fetchone()
        if row is None:
            return None
        return Prompt(
            prompt_id=row["prompt_id"],
            name=row["name"],
            description=row["description"],
            current_version=row["current_version"],
            tags=json.loads(row["tags"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=row["status"],
        )

    def list_prompts(self, status: Optional[str] = None) -> list[Prompt]:
        """列出提示词，可按状态过滤"""
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM prompts WHERE status = ? ORDER BY updated_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM prompts ORDER BY updated_at DESC"
                ).fetchall()
        return [
            Prompt(
                prompt_id=r["prompt_id"],
                name=r["name"],
                description=r["description"],
                current_version=r["current_version"],
                tags=json.loads(r["tags"]),
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
                status=r["status"],
            )
            for r in rows
        ]

    # ---- Version Management ----

    def save_version(self, version: PromptVersion) -> None:
        """保存提示词版本"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO prompt_versions
                   (version_id, prompt_id, template_id, template_content,
                    llm_config, commit_message, author, created_at, parent_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (version.version_id, version.prompt_id,
                 version.template_id, version.template_content,
                 json.dumps(version.llm_config),
                 version.commit_message, version.author,
                 version.created_at.isoformat(),
                 version.parent_version),
            )

    def get_version(self, prompt_id: str, version_id: str) -> Optional[PromptVersion]:
        """获取指定版本的详细信息"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM prompt_versions WHERE prompt_id = ? AND version_id = ?",
                (prompt_id, version_id),
            ).fetchone()
        if row is None:
            return None
        return PromptVersion(
            version_id=row["version_id"],
            prompt_id=row["prompt_id"],
            template_id=row["template_id"],
            template_content=row["template_content"],
            llm_config=json.loads(row["llm_config"]),
            commit_message=row["commit_message"],
            author=row["author"],
            created_at=datetime.fromisoformat(row["created_at"]),
            parent_version=row["parent_version"],
        )

    def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        """按时间倒序列出提示词的所有版本"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM prompt_versions
                   WHERE prompt_id = ?
                   ORDER BY created_at DESC""",
                (prompt_id,),
            ).fetchall()
        return [
            PromptVersion(
                version_id=r["version_id"],
                prompt_id=r["prompt_id"],
                template_id=r["template_id"],
                template_content=r["template_content"],
                llm_config=json.loads(r["llm_config"]),
                commit_message=r["commit_message"],
                author=r["author"],
                created_at=datetime.fromisoformat(r["created_at"]),
                parent_version=r["parent_version"],
            )
            for r in rows
        ]

    def get_version_history(self, prompt_id: str) -> list[dict]:
        """获取版本历史摘要（用于展示版本树）"""
        versions = self.list_versions(prompt_id)
        return [
            {
                "version": v.version_id,
                "author": v.author,
                "message": v.commit_message,
                "parent": v.parent_version,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]
