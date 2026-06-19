"""Rule kiểm tra thụt đầu dòng (first-line indent).

Bỏ qua đoạn căn giữa (tiêu đề) — không yêu cầu thụt đầu dòng.
"""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec


def _first_line_cm(para) -> float:
    fli = para.paragraph_format.first_line_indent
    return fli.cm if fli is not None else 0.0


class IndentRule:
    code = "INDENT"
    name = "Thụt đầu dòng"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        lo, hi = spec.indent.min_cm, spec.indent.max_cm
        issues: list[Issue] = []
        for i, para in enumerate(doc.paragraphs):
            if not para.text.strip():
                continue
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                continue
            cm = _first_line_cm(para)
            if cm + 0.01 < lo:
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: chưa thụt đầu dòng (cần {lo:g}–{hi:g}cm)",
                    suggestion=f"Thụt đầu dòng {spec.indent.fix_to_cm:g}cm",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Cm

        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                continue
            if _first_line_cm(para) + 0.01 < spec.indent.min_cm:
                para.paragraph_format.first_line_indent = Cm(spec.indent.fix_to_cm)
