"""Rule viết hoa đầu câu (deterministic).

CHỈ xử lý viết hoa chữ cái đầu MỖI CÂU (đầu đoạn + sau dấu . ? !).
Các quy tắc viết hoa NGỮ NGHĨA — tên riêng, cơ quan/chức vụ, lễ hội/sự kiện
(vd "Nguyễn Văn Long", "Bộ Tài chính", "Tết Nguyên đán") — KHÔNG deterministic,
cần phân tích ngữ nghĩa bằng Claude (GĐ3). Xem docs/quy-chuan-nd30.md.

Lưu ý: rule này SỬA NỘI DUNG văn bản (viết hoa 1 ký tự), khác các rule định dạng.
"""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec

_SENTENCE_END = (".", "!", "?")


def _sentence_initial_indices(text: str) -> list[int]:
    """Vị trí (index) chữ cái đầu của mỗi câu trong đoạn."""
    idxs: list[int] = []
    expect = True  # đầu đoạn là đầu câu
    for i, ch in enumerate(text):
        if expect and ch.isalpha():
            idxs.append(i)
            expect = False
        elif ch in _SENTENCE_END:
            expect = True
    return idxs


def _fix_paragraph(para) -> None:
    """Viết hoa chữ cái đầu mỗi câu, đi qua từng run để giữ định dạng."""
    expect = True
    for run in para.runs:
        if not run.text:
            continue
        chars = list(run.text)
        for k, ch in enumerate(chars):
            if expect and ch.isalpha():
                chars[k] = ch.upper()
                expect = False
            elif ch in _SENTENCE_END:
                expect = True
        run.text = "".join(chars)


class CapitalizationRule:
    code = "CAPITALIZATION"
    name = "Viết hoa đầu câu"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            if not text.strip():
                continue
            bad = sum(1 for j in _sentence_initial_indices(text) if text[j].islower())
            if bad:
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1}: chưa viết hoa đầu câu ({bad} chỗ)",
                    suggestion="Viết hoa chữ cái đầu mỗi câu",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        for para in doc.paragraphs:
            if para.text.strip():
                _fix_paragraph(para)
