"""Kiểu dữ liệu dùng chung cho rule engine.

- TemplateSpec: đặc tả một bộ quy chuẩn định dạng (preset hoặc custom).
- Issue: một lỗi định dạng phát hiện được.
- ParsedDoc: bọc python-docx Document để truyền cho các rule.
- AnalysisReport: kết quả phân tích thuần (chưa gắn DB).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


# --- Đặc tả quy chuẩn (TemplateSpec) ---

class FontSpec(BaseModel):
    name: str = "Times New Roman"
    size_pt_min: float = 13.0
    size_pt_max: float = 14.0
    fix_size_pt: float = 14.0  # cỡ chữ dùng khi auto-fix (GĐ2)


class MarginRange(BaseModel):
    min_cm: float
    max_cm: float
    fix_to_cm: float  # giá trị đặt khi auto-fix (GĐ2)


class MarginSpec(BaseModel):
    top: MarginRange
    bottom: MarginRange
    left: MarginRange
    right: MarginRange


class LineSpacingSpec(BaseModel):
    min: float = 1.5
    fix_to: float = 1.5


class PageSpec(BaseModel):
    width_mm: float = 210.0          # A4
    height_mm: float = 297.0
    tolerance_mm: float = 1.0
    orientation: str = "portrait"    # portrait | landscape


class IndentSpec(BaseModel):
    min_cm: float = 1.0              # thụt đầu dòng 1.0–1.27cm
    max_cm: float = 1.27
    fix_to_cm: float = 1.0


class AlignmentSpec(BaseModel):
    target: str = "justify"          # justify | left | center | right


class TemplateSpec(BaseModel):
    """Bộ quy chuẩn định dạng. Serialize được sang JSON để lưu DB / file preset."""

    key: str
    name: str
    font: FontSpec = Field(default_factory=FontSpec)
    margins: MarginSpec
    line_spacing: LineSpacingSpec = Field(default_factory=LineSpacingSpec)
    page: PageSpec = Field(default_factory=PageSpec)
    indent: IndentSpec = Field(default_factory=IndentSpec)
    alignment: AlignmentSpec = Field(default_factory=AlignmentSpec)


# --- Lỗi & báo cáo ---

class Issue(BaseModel):
    rule_code: str
    message: str
    suggestion: str = ""
    paragraph_index: int | None = None
    page_number: int | None = None


class AnalysisReport(BaseModel):
    score: float
    total_errors: int
    by_rule: dict[str, int] = Field(default_factory=dict)
    issues: list[Issue] = Field(default_factory=list)


# --- Tài liệu đã parse ---

@dataclass
class ParsedDoc:
    """Bọc python-docx Document. `document` để Any nhằm tránh import cứng python-docx ở tầng types."""

    document: Any

    @property
    def paragraphs(self):
        return self.document.paragraphs

    @property
    def sections(self):
        return self.document.sections

    @property
    def styles(self):
        return self.document.styles
