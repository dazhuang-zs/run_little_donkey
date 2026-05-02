"""
调用追踪器：记录每次 LLM 调用的详细信息，用于性能分析和问题排查。
"""
from __future__ import annotations
import sqlite3
import json
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any
from collections import defaultdict


@dataclass
class CallRecord:
    """单次 LLM 调用的完整记录"""
    call_id: str
    prompt_id: str
    version_id: str
    template_name: str
    model: str
    prompt_text: str = ""
    response_text: str = ""
    latency_ms: float = 0.0
    token_count: int = 0
    status: str = "success"       # success / error / timeout
    error_message: str = ""
    created_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class CallTracker:
    """
    调用追踪器：记录每次 LLM 调用的元数据。

    生产环境建议:
    - 异步写入避免阻塞推理流程
    - 定期归档历史数据
    - 设置保留期限
    """

    def __init__(self, db_path: str = "prompt_engine.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS call_logs (
                    call_id TEXT PRIMARY KEY,
                    prompt_id TEXT,
                    version_id TEXT,
                    template_name TEXT,
                    model TEXT,
                    prompt_text TEXT DEFAULT '',
                    response_text TEXT DEFAULT '',
                    latency_ms REAL DEFAULT 0,
                    token_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    extra TEXT DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_calls_prompt
                    ON call_logs(prompt_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_calls_status
                    ON call_logs(status);
                CREATE INDEX IF NOT EXISTS idx_calls_created
                    ON call_logs(created_at);
            """)

    def record(self, record: CallRecord) -> None:
        """记录一次调用"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO call_logs
                   (call_id, prompt_id, version_id, template_name, model,
                    prompt_text, response_text, latency_ms, token_count,
                    status, error_message, created_at, extra)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record.call_id, record.prompt_id, record.version_id,
                 record.template_name, record.model,
                 record.prompt_text, record.response_text,
                 record.latency_ms, record.token_count,
                 record.status, record.error_message,
                 record.created_at or datetime.now().isoformat(),
                 json.dumps(record.extra)),
            )

    def query(
        self,
        prompt_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CallRecord]:
        """查询调用记录，支持按 prompt_id 和 status 过滤"""
        conditions = []
        params = []

        if prompt_id:
            conditions.append("prompt_id = ?")
            params.append(prompt_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM call_logs WHERE {where_clause}"
                " ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()

        return [
            CallRecord(
                call_id=r["call_id"],
                prompt_id=r["prompt_id"],
                version_id=r["version_id"],
                template_name=r["template_name"],
                model=r["model"],
                prompt_text=r["prompt_text"],
                response_text=r["response_text"],
                latency_ms=r["latency_ms"],
                token_count=r["token_count"],
                status=r["status"],
                error_message=r["error_message"],
                created_at=r["created_at"],
                extra=json.loads(r["extra"]),
            )
            for r in rows
        ]

    def get_performance_summary(
        self,
        prompt_id: str,
        since: str | None = None,
    ) -> dict:
        """获取指定提示词在时间段内的性能摘要"""
        conditions = ["prompt_id = ?"]
        params = [prompt_id]

        if since:
            conditions.append("created_at >= ?")
            params.append(since)

        where = " AND ".join(conditions)

        with self._get_conn() as conn:
            # 平均延迟和 P95
            row = conn.execute(
                f"""SELECT
                    COUNT(*) as total_calls,
                    AVG(latency_ms) as avg_latency,
                    AVG(token_count) as avg_tokens,
                    SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as error_count
                FROM call_logs WHERE {where}""",
                params,
            ).fetchone()

            # P95 延迟
            rows = conn.execute(
                f"""SELECT latency_ms FROM call_logs
                    WHERE {where} ORDER BY latency_ms""",
                params,
            ).fetchall()

            latencies = [r["latency_ms"] for r in rows]
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

            return {
                "prompt_id": prompt_id,
                "total_calls": row["total_calls"] or 0,
                "avg_latency_ms": round(row["avg_latency"] or 0, 1),
                "p95_latency_ms": round(p95, 1),
                "avg_tokens": round(row["avg_tokens"] or 0, 1),
                "error_rate": round(
                    (row["error_count"] or 0) / max(row["total_calls"], 1) * 100,
                    2,
                ),
            }

    def get_error_trend(self, hours: int = 24) -> list[dict]:
        """按小时统计错误率趋势"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT
                    substr(created_at, 1, 13) as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as errors
                FROM call_logs
                WHERE created_at >= datetime('now', ?)
                GROUP BY hour
                ORDER BY hour""",
                (f"-{hours} hours",),
            ).fetchall()

        return [
            {
                "hour": r["hour"],
                "total_calls": r["total"],
                "error_count": r["errors"],
                "error_rate": round(r["errors"] / max(r["total"], 1) * 100, 2),
            }
            for r in rows
        ]
