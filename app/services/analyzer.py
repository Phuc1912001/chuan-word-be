"""Analyzer: chạy rule engine trên một tài liệu và chấm điểm.

Hàm `analyze`/`analyze_file` là THUẦN (không đụng DB) để dễ test và tái dùng
trong Celery worker (GĐ0). Việc lưu kết quả vào DB do tầng endpoint/worker đảm nhiệm.
"""

from __future__ import annotations

from app.rules.registry import default_rules
from app.rules.types import AnalysisReport, Issue, ParsedDoc, TemplateSpec
from app.services.docx_parser import load_docx

# Trọng số trừ điểm tạm thời cho mỗi lỗi (sẽ tinh chỉnh theo loại lỗi sau).
ISSUE_PENALTY = 5.0


def analyze(doc: ParsedDoc, spec: TemplateSpec, rules=None) -> AnalysisReport:
    rules = rules if rules is not None else default_rules()

    issues: list[Issue] = []
    for rule in rules:
        issues.extend(rule.check(doc, spec))

    by_rule: dict[str, int] = {}
    for issue in issues:
        by_rule[issue.rule_code] = by_rule.get(issue.rule_code, 0) + 1

    total = len(issues)
    score = max(0.0, round(100.0 - total * ISSUE_PENALTY, 1))

    return AnalysisReport(score=score, total_errors=total, by_rule=by_rule, issues=issues)


def analyze_file(path: str, spec: TemplateSpec, rules=None) -> AnalysisReport:
    return analyze(load_docx(path), spec, rules)
