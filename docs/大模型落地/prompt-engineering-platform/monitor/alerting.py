"""
异常检测与告警模块：监控提示词在生产环境中的异常行为。
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from datetime import datetime, timedelta


@dataclass
class AlertRule:
    """告警规则定义"""
    name: str
    metric: str              # latency_p95 / error_rate / token_count / drift_score
    operator: str            # gt / lt / gte / lte
    threshold: float
    window_minutes: int = 10
    enabled: bool = True


@dataclass
class AlertEvent:
    """告警事件"""
    rule_name: str
    metric: str
    actual_value: float
    threshold: float
    triggered_at: str
    severity: str = "warning"   # info / warning / critical


class AnomalyDetector:
    """
    异常检测器：监控提示词在生产环境中的表现退化。

    检测维度:
    1. 延迟突增 - 模型响应变慢
    2. 错误率上升 - API 调用异常增多
    3. Token 消耗异常 - 输出长度突变（提示词漂移的信号）
    4. 空响应/拒绝回答 - 安全机制误触发
    """

    def __init__(self, tracker, alert_handler: Callable | None = None):
        """
        参数:
            tracker: CallTracker 实例，用于获取历史数据
            alert_handler: 告警处理函数，如发送邮件、钉钉消息等
        """
        self.tracker = tracker
        self.alert_handler = alert_handler

    def check_latency_anomaly(
        self,
        prompt_id: str,
        threshold_ms: float = 5000,
        baseline_hours: int = 24,
    ) -> list[AlertEvent]:
        """
        检查延迟异常：当前延迟 vs 历史基线。

        典型场景:
        - 模型升级后延迟突增
        - 某版本提示词过长导致延迟飙升
        - 后端 API 性能退化
        """
        events: list[AlertEvent] = []

        # 获取基线数据（24 小时内）
        since = (datetime.now() - timedelta(hours=baseline_hours)).isoformat()
        summary = self.tracker.get_performance_summary(prompt_id, since=since)

        p95 = summary.get("p95_latency_ms", 0)
        if p95 > threshold_ms:
            events.append(AlertEvent(
                rule_name="latency_p95_threshold",
                metric="latency_p95_ms",
                actual_value=p95,
                threshold=threshold_ms,
                triggered_at=datetime.now().isoformat(),
                severity="warning" if p95 < threshold_ms * 2 else "critical",
            ))

        return events

    def check_error_rate(
        self,
        prompt_id: str,
        threshold_percent: float = 5.0,
        window_minutes: int = 10,
    ) -> list[AlertEvent]:
        """
        检查错误率是否超过阈值。

        典型场景:
        - API key 过期导致大量 401
        - 模型负载过高导致 429
        - 提示词格式错误导致 400
        """
        events: list[AlertEvent] = []
        since = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        summary = self.tracker.get_performance_summary(prompt_id, since=since)

        error_rate = summary.get("error_rate", 0)
        if error_rate > threshold_percent:
            events.append(AlertEvent(
                rule_name="error_rate_threshold",
                metric="error_rate_percent",
                actual_value=error_rate,
                threshold=threshold_percent,
                triggered_at=datetime.now().isoformat(),
                severity="critical" if error_rate > threshold_percent * 2 else "warning",
            ))

        return events

    def check_token_drift(
        self,
        prompt_id: str,
        baseline_tokens: float = 500,
        deviation_ratio: float = 0.5,
    ) -> list[AlertEvent]:
        """
        检查 Token 消耗漂移：平均 token 数偏离基线超过指定比例。

        这是检测"提示词漂移"的关键指标。
        当输出长度突然大幅变化时，很可能提示词的效果已经变了。
        """
        events: list[AlertEvent] = []
        summary = self.tracker.get_performance_summary(prompt_id)

        avg_tokens = summary.get("avg_tokens", 0)
        if avg_tokens > 0 and baseline_tokens > 0:
            deviation = abs(avg_tokens - baseline_tokens) / baseline_tokens
            if deviation > deviation_ratio:
                events.append(AlertEvent(
                    rule_name="token_drift",
                    metric="token_deviation_ratio",
                    actual_value=round(deviation, 4),
                    threshold=deviation_ratio,
                    triggered_at=datetime.now().isoformat(),
                    severity="warning",
                ))

        return events

    def run_all_checks(
        self,
        prompt_id: str,
        config: dict | None = None,
    ) -> list[AlertEvent]:
        """
        运行所有检查项。

        config 可自定义阈值:
        {
            "latency_threshold_ms": 5000,
            "error_rate_threshold": 5.0,
            "baseline_tokens": 500,
            "token_drift_ratio": 0.5,
        }
        """
        cfg = config or {}
        all_events: list[AlertEvent] = []

        all_events.extend(self.check_latency_anomaly(
            prompt_id,
            threshold_ms=cfg.get("latency_threshold_ms", 5000),
        ))
        all_events.extend(self.check_error_rate(
            prompt_id,
            threshold_percent=cfg.get("error_rate_threshold", 5.0),
        ))
        all_events.extend(self.check_token_drift(
            prompt_id,
            baseline_tokens=cfg.get("baseline_tokens", 500),
            deviation_ratio=cfg.get("token_drift_ratio", 0.5),
        ))

        # 触发告警处理
        for event in all_events:
            if self.alert_handler:
                self.alert_handler(event)

        return all_events
