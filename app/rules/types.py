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
    # Web chốt: "Single đến tối đa 1.5 lines" → hợp lệ trong [min, max], lỗi nếu > max.
    min: float = 1.0
    max: float = 1.5
    fix_to: float = 1.5


class ParagraphSpacingSpec(BaseModel):
    """Giãn đoạn: khoảng cách giữa các đoạn tối thiểu 6pt (đo qua space_after)."""

    space_after_pt_min: float = 6.0
    fix_to_pt: float = 6.0


# Nhãn thành phần văn bản (do classifier gán). Xem app/rules/classifier.py.
COMP_QUOC_HIEU = "quoc_hieu"
COMP_TIEU_NGU = "tieu_ngu"
COMP_DIA_DANH_NGAY = "dia_danh_ngay"
COMP_TEN_LOAI_VB = "ten_loai_vb"
COMP_NOI_DUNG = "noi_dung"
COMP_HO_TEN_KY = "ho_ten_ky"
COMP_KHAC = "khac"  # tiêu đề mục/danh sách/không rõ → coi như body, không ép kiểu

COMPONENT_LABELS = {
    COMP_QUOC_HIEU: "Quốc hiệu",
    COMP_TIEU_NGU: "Tiêu ngữ",
    COMP_DIA_DANH_NGAY: "Địa danh, ngày tháng",
    COMP_TEN_LOAI_VB: "Tên loại văn bản",
    COMP_NOI_DUNG: "Nội dung",
    COMP_HO_TEN_KY: "Họ tên người ký",
    COMP_KHAC: "Văn bản",
}


class ComponentSpec(BaseModel):
    """Đặc tả cỡ/kiểu chữ cho một thành phần văn bản (bảng III, Nghị định 30)."""

    size_pt_min: float
    size_pt_max: float
    fix_size_pt: float
    bold: bool | None = None        # None = không ràng buộc
    italic: bool | None = None
    first_line_indent: bool = False  # có yêu cầu thụt đầu dòng không


def _default_components() -> dict[str, ComponentSpec]:
    return {
        COMP_QUOC_HIEU: ComponentSpec(size_pt_min=12, size_pt_max=13, fix_size_pt=13, bold=True, italic=False),
        COMP_TIEU_NGU: ComponentSpec(size_pt_min=13, size_pt_max=14, fix_size_pt=14, bold=True, italic=False),
        COMP_DIA_DANH_NGAY: ComponentSpec(size_pt_min=13, size_pt_max=14, fix_size_pt=14, italic=True),
        COMP_TEN_LOAI_VB: ComponentSpec(size_pt_min=14, size_pt_max=15, fix_size_pt=14, bold=True, italic=False),
        COMP_NOI_DUNG: ComponentSpec(size_pt_min=13, size_pt_max=14, fix_size_pt=14, first_line_indent=True),
        COMP_HO_TEN_KY: ComponentSpec(size_pt_min=13, size_pt_max=14, fix_size_pt=14, bold=True),
        COMP_KHAC: ComponentSpec(size_pt_min=13, size_pt_max=14, fix_size_pt=14),
    }


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
    paragraph_spacing: ParagraphSpacingSpec = Field(default_factory=ParagraphSpacingSpec)
    page: PageSpec = Field(default_factory=PageSpec)
    indent: IndentSpec = Field(default_factory=IndentSpec)
    alignment: AlignmentSpec = Field(default_factory=AlignmentSpec)
    components: dict[str, ComponentSpec] = Field(default_factory=_default_components)

    def component(self, label: str) -> ComponentSpec:
        """Lấy spec của một thành phần; fallback về 'noi_dung' rồi 'khac'."""
        from app.rules.types import COMP_KHAC, COMP_NOI_DUNG

        return (
            self.components.get(label)
            or self.components.get(COMP_NOI_DUNG)
            or self.components.get(COMP_KHAC)
        )


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
