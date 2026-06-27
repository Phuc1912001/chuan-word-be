"""Rule giãn đoạn (PARAGRAPH_SPACING) — khoảng cách giữa các đoạn ≥ 6pt.

CHỈ áp cho đoạn NỘI DUNG ở CẤP THÂN (không vào bảng, không header/footer, không
các thành phần cấu trúc như Quốc hiệu/tiêu ngữ/tên loại VB/chữ ký). KHÔNG đụng
style Normal (vì ô bảng thừa kế Normal → set Normal sẽ làm bảng phình cao).

CHECK bảo thủ: chỉ báo khi đoạn nội dung có space_after TƯỜNG MINH < 6pt. FIX đặt
space_after = 6pt cho đoạn nội dung đang thiếu (đo theo giá trị hiệu lực).
"""

from __future__ import annotations

from app.rules.classifier import classify_top_level
from app.rules.types import COMP_NOI_DUNG, Issue, ParsedDoc, TemplateSpec

_EPS = 0.01


def _effective_after_pt(para, document) -> float | None:
    sa = para.paragraph_format.space_after
    if sa is not None:
        return sa.pt
    style = getattr(para, "style", None)
    while style is not None:
        s = style.paragraph_format.space_after
        if s is not None:
            return s.pt
        style = getattr(style, "base_style", None)
    return None


class ParagraphSpacingRule:
    code = "PARAGRAPH_SPACING"
    name = "Giãn đoạn"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        min_pt = spec.paragraph_spacing.space_after_pt_min
        issues: list[Issue] = []
        for i, (para, label) in enumerate(classify_top_level(doc)):
            if label != COMP_NOI_DUNG:
                continue
            after = para.paragraph_format.space_after  # chỉ xét giá trị tường minh
            if after is not None and after.pt < min_pt - _EPS:
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: giãn đoạn {after.pt:g}pt nhỏ hơn chuẩn {min_pt:g}pt",
                    suggestion=f"Đặt khoảng cách sau đoạn {spec.paragraph_spacing.fix_to_pt:g}pt",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.shared import Pt

        document = doc.document
        min_pt = spec.paragraph_spacing.space_after_pt_min
        fix_pt = spec.paragraph_spacing.fix_to_pt
        for para, label in classify_top_level(doc):
            if label != COMP_NOI_DUNG:
                continue
            eff = _effective_after_pt(para, document)
            if eff is None or eff < min_pt - _EPS:
                para.paragraph_format.space_after = Pt(fix_pt)
