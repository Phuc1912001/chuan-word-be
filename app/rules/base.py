"""Interface chung cho mọi rule định dạng."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.rules.types import Issue, ParsedDoc, TemplateSpec


@runtime_checkable
class Rule(Protocol):
    code: str   # mã rule, vd "FONT", "MARGIN" — khớp cột rule_code trong DB
    name: str   # tên hiển thị tiếng Việt

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        """Phát hiện lỗi. Trả về danh sách rỗng nếu đạt chuẩn."""
        ...

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        """Sửa định dạng tại chỗ cho đạt chuẩn. CHỈ đổi format, KHÔNG đổi nội dung. (Dùng ở GĐ2.)"""
        ...
