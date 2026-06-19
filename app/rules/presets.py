"""Các bộ quy chuẩn dựng sẵn (preset).

Custom template (do user upload file mẫu) sẽ sinh ra cùng cấu trúc TemplateSpec ở GĐ4.
"""

from app.rules.types import (
    FontSpec,
    LineSpacingSpec,
    MarginRange,
    MarginSpec,
    TemplateSpec,
)

# Nghị định 30/2020/NĐ-CP — văn bản hành chính:
#   font Times New Roman cỡ 13–14; lề trên/dưới 20–25mm, trái 30–35mm, phải 15–20mm.
NGHI_DINH_30 = TemplateSpec(
    key="nghi-dinh-30",
    name="Nghị định 30/2020/NĐ-CP (văn bản hành chính)",
    font=FontSpec(name="Times New Roman", size_pt_min=13.0, size_pt_max=14.0, fix_size_pt=14.0),
    margins=MarginSpec(
        top=MarginRange(min_cm=2.0, max_cm=2.5, fix_to_cm=2.0),
        bottom=MarginRange(min_cm=2.0, max_cm=2.5, fix_to_cm=2.0),
        left=MarginRange(min_cm=3.0, max_cm=3.5, fix_to_cm=3.0),
        right=MarginRange(min_cm=1.5, max_cm=2.0, fix_to_cm=2.0),
    ),
    line_spacing=LineSpacingSpec(min=1.5, fix_to=1.5),
)

PRESETS: dict[str, TemplateSpec] = {
    NGHI_DINH_30.key: NGHI_DINH_30,
}

DEFAULT_PRESET_KEY = "nghi-dinh-30"


def get_preset(key: str | None = None) -> TemplateSpec:
    """Lấy preset theo key; mặc định Nghị định 30 nếu key None/không hợp lệ."""
    return PRESETS.get(key or DEFAULT_PRESET_KEY, NGHI_DINH_30)
