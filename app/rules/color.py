"""Rule màu chữ (COLOR) — văn bản phải màu đen.

CHECK bảo thủ: chỉ báo khi run có màu RGB tường minh KHÁC đen (bỏ qua auto/theme
và run không đặt màu). FIX đưa các run đó về đen. Duyệt mọi đoạn.
"""

from __future__ import annotations

from app.rules.docx_iter import iter_all_paragraphs
from app.rules.types import Issue, ParsedDoc, TemplateSpec

_BLACK = "000000"


def _explicit_rgb(run) -> str | None:
    color = run.font.color
    if color is None:
        return None
    try:
        rgb = color.rgb  # None nếu type là auto/theme/none
    except Exception:
        return None
    return str(rgb) if rgb is not None else None


class ColorRule:
    code = "COLOR"
    name = "Màu chữ"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for i, para in enumerate(iter_all_paragraphs(doc)):
            for run in para.runs:
                if not run.text.strip():
                    continue
                rgb = _explicit_rgb(run)
                if rgb is not None and rgb.upper() != _BLACK:
                    issues.append(Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: màu chữ #{rgb} không phải đen",
                        suggestion="Đặt màu chữ đen",
                    ))
                    break
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.shared import RGBColor

        for para in iter_all_paragraphs(doc):
            for run in para.runs:
                if not run.text.strip():
                    continue
                rgb = _explicit_rgb(run)
                if rgb is not None and rgb.upper() != _BLACK:
                    run.font.color.rgb = RGBColor(0, 0, 0)
