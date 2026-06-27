"""Rule giãn dòng (LINE_SPACING).

Chuẩn (chốt theo web): "Single đến tối đa 1.5 lines" → hợp lệ trong [min, max]
(mặc định 1.0–1.5); BÁO LỖI nếu giãn dòng kiểu Multiple > 1.5; auto-fix kéo
về 1.5. Giãn dòng kiểu cố định (Exactly/At least, đơn vị pt) KHÔNG so sánh được
theo "số dòng" nên bỏ qua, tránh phá vỡ bố cục bảng/đặc thù.

Duyệt mọi đoạn (thân + bảng + header/footer).
"""

from __future__ import annotations

from app.rules.docx_iter import iter_all_paragraphs
from app.rules.types import Issue, ParsedDoc, TemplateSpec

_EPS = 1e-6


def _as_multiple(value) -> float | None:
    """Trả float nếu line spacing là kiểu 'Multiple' (1.0, 1.5...); None nếu là
    Length (EMU, kiểu Exactly/At least) hoặc chưa đặt."""
    if value is None:
        return None
    if hasattr(value, "emu"):  # Length → giãn dòng cố định theo pt, bỏ qua
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


class LineSpacingRule:
    code = "LINE_SPACING"
    name = "Giãn dòng"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        max_ls = spec.line_spacing.max

        try:
            normal_ls = _as_multiple(doc.styles["Normal"].paragraph_format.line_spacing)
        except KeyError:
            normal_ls = None
        if normal_ls is not None and normal_ls > max_ls + _EPS:
            issues.append(Issue(
                rule_code=self.code,
                message=f"Giãn dòng mặc định {normal_ls:g} vượt tối đa {max_ls:g}",
                suggestion=f"Đặt giãn dòng {spec.line_spacing.fix_to:g}",
            ))

        for i, para in enumerate(iter_all_paragraphs(doc)):
            ls = _as_multiple(para.paragraph_format.line_spacing)
            if ls is not None and ls > max_ls + _EPS:
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: giãn dòng {ls:g} vượt tối đa {max_ls:g}",
                    suggestion=f"Đặt giãn dòng {spec.line_spacing.fix_to:g}",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        max_ls = spec.line_spacing.max
        fix_to = spec.line_spacing.fix_to

        try:
            nf = doc.styles["Normal"].paragraph_format
            n_ls = _as_multiple(nf.line_spacing)
            if n_ls is not None and n_ls > max_ls + _EPS:
                nf.line_spacing = fix_to
        except KeyError:
            pass

        for para in iter_all_paragraphs(doc):
            ls = _as_multiple(para.paragraph_format.line_spacing)
            if ls is not None and ls > max_ls + _EPS:
                para.paragraph_format.line_spacing = fix_to
