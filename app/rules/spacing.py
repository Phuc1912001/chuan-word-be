"""Rule kiểm tra giãn dòng (line spacing)."""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec


def _as_multiple(value) -> float | None:
    """python-docx trả float cho line spacing kiểu 'Multiple' (vd 1.0, 1.5),
    hoặc Length (int EMU) cho kiểu 'Exactly/At least'. Chỉ xét trường hợp Multiple.
    """
    # Length là lớp con của int (EMU) → loại ra bằng cách kiểm tra có thuộc tính .emu
    if value is None:
        return None
    if hasattr(value, "emu"):  # Length → bỏ qua (giãn dòng cố định theo pt)
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


class LineSpacingRule:
    code = "LINE_SPACING"
    name = "Giãn dòng"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        min_ls = spec.line_spacing.min

        # Mức tài liệu (style Normal)
        try:
            normal_ls = _as_multiple(doc.styles["Normal"].paragraph_format.line_spacing)
        except KeyError:
            normal_ls = None
        if normal_ls is not None and normal_ls + 1e-6 < min_ls:
            issues.append(Issue(
                rule_code=self.code,
                message=f"Giãn dòng mặc định {normal_ls:g} nhỏ hơn chuẩn {min_ls:g}",
                suggestion=f"Đặt giãn dòng {spec.line_spacing.fix_to:g}",
            ))

        # Mức từng đoạn (override)
        for i, para in enumerate(doc.paragraphs):
            ls = _as_multiple(para.paragraph_format.line_spacing)
            if ls is not None and ls + 1e-6 < min_ls:
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: giãn dòng {ls:g} nhỏ hơn chuẩn {min_ls:g}",
                    suggestion=f"Đặt giãn dòng {spec.line_spacing.fix_to:g}",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        fix_to = spec.line_spacing.fix_to
        try:
            doc.styles["Normal"].paragraph_format.line_spacing = fix_to
        except KeyError:
            pass
        for para in doc.paragraphs:
            if _as_multiple(para.paragraph_format.line_spacing) is not None:
                para.paragraph_format.line_spacing = fix_to
