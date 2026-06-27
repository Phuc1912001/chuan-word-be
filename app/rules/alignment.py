"""Rule căn lề đoạn văn (căn đều hai lề - justify).

Chỉ flag đoạn căn TRÁI/PHẢI rõ ràng. Bỏ qua đoạn căn GIỮA (tiêu đề) và đoạn
không set alignment (kế thừa).

GUARD chống "chữ cách xa nhau": KHÔNG căn đều đoạn chứa một "từ" quá dài không
ngắt được (URL dài, mã, chuỗi liền) — vì justify sẽ kéo giãn các chữ còn lại
trên dòng tạo khoảng trắng lớn. Đoạn như vậy để căn TRÁI cho gọn.
"""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec

# Ngưỡng độ dài 1 token coi là "quá dài để căn đều" (từ tiếng Việt hiếm khi >8).
_LONG_TOKEN = 30


def _has_long_token(text: str) -> bool:
    return any(len(tok) > _LONG_TOKEN for tok in text.split())


class AlignmentRule:
    code = "ALIGNMENT"
    name = "Căn lề đoạn văn"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        if spec.alignment.target != "justify":
            return []
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        issues: list[Issue] = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            if not text.strip() or _has_long_token(text):
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
            text = para.text
            if not text.strip():
                continue
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                continue  # giữ nguyên tiêu đề căn giữa
            if _has_long_token(text):
                # Đoạn có chuỗi quá dài → căn trái để tránh kéo giãn chữ.
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                continue
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
