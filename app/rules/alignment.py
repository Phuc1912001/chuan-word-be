"""Rule kiểm tra căn lề đoạn văn (căn đều hai lề).

Chỉ flag đoạn căn TRÁI/PHẢI rõ ràng. Bỏ qua đoạn căn GIỮA (thường là tiêu đề)
và đoạn không set alignment (kế thừa). Đây là cách giảm báo nhầm khi chưa có
nhận diện cấu trúc (tiêu đề/nội dung) — xem docs/quy-chuan-nd30.md.
"""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec


class AlignmentRule:
    code = "ALIGNMENT"
    name = "Căn lề đoạn văn"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        if spec.alignment.target != "justify":
            return []
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        issues: list[Issue] = []
        for i, para in enumerate(doc.paragraphs):
            if not para.text.strip():
                continue
            if para.alignment in (WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT):
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: chưa căn đều hai lề",
                    suggestion="Căn đều hai lề (justify)",
                ))

        try:
            normal_align = doc.styles["Normal"].paragraph_format.alignment
        except KeyError:
            normal_align = None
        if normal_align in (WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT):
            issues.append(Issue(
                rule_code=self.code,
                message="Căn lề mặc định chưa phải căn đều hai lề",
                suggestion="Đặt căn đều hai lề (justify)",
            ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        if spec.alignment.target != "justify":
            return
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                continue  # giữ nguyên tiêu đề căn giữa
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
