"""Tests for data models."""

from ai_code_reviewer.models import (
    ReviewFinding, ReviewReport, Severity, ReviewDimension,
)


def test_severity_values():
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.LOW.value == "low"


def test_review_finding_to_dict():
    finding = ReviewFinding(
        dimension=ReviewDimension.SECURITY,
        severity=Severity.HIGH,
        file_path="src/app.py",
        line_start=10,
        line_end=15,
        title="SQL注入风险",
        description="直接拼接SQL查询",
        suggestion="使用参数化查询",
        code_snippet="cursor.execute(f\"SELECT * FROM users WHERE id = {id}\")",
        confidence=0.95,
    )
    d = finding.to_dict()
    assert d["dimension"] == "security"
    assert d["severity"] == "high"
    assert d["title"] == "SQL注入风险"


def test_report_summary():
    findings = [
        ReviewFinding(
            dimension=ReviewDimension.SECURITY,
            severity=Severity.CRITICAL,
            file_path="a.py", line_start=1, line_end=5,
            title="T1", description="D1", suggestion="S1",
            code_snippet="", confidence=0.9,
        ),
        ReviewFinding(
            dimension=ReviewDimension.PERFORMANCE,
            severity=Severity.MEDIUM,
            file_path="a.py", line_start=10, line_end=12,
            title="T2", description="D2", suggestion="S2",
            code_snippet="", confidence=0.7,
        ),
    ]

    report = ReviewReport(
        commit_sha="abc123",
        branch="main",
        files_changed=1,
        total_findings=2,
        findings=findings,
    )

    assert report.total_findings == 2
    assert len(report.get_findings_by_severity(Severity.CRITICAL)) == 1
    assert len(report.get_findings_by_severity(Severity.MEDIUM)) == 1
    assert len(report.get_findings_by_dimension(ReviewDimension.SECURITY)) == 1


def test_report_to_dict():
    findings = [
        ReviewFinding(
            dimension=ReviewDimension.SECURITY,
            severity=Severity.CRITICAL,
            file_path="a.py", line_start=1, line_end=5,
            title="T1", description="D1", suggestion="S1",
            code_snippet="", confidence=0.9,
        ),
    ]
    report = ReviewReport(
        commit_sha="abc", branch="main",
        files_changed=1, total_findings=1, findings=findings,
    )
    d = report.to_dict()
    assert d["commit_sha"] == "abc"
    assert len(d["findings"]) == 1
