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
    """Vị trí chữ cái đầu MỖI CÂU: đầu đoạn, hoặc sau dấu . ! ? CÓ khoảng trắng
    theo sau. Yêu cầu khoảng trắng để KHÔNG viết hoa nhầm trong 'GMO-Z.com',
    '1.Tên mục', '3.14', 'a.b' — các dấu chấm không phải kết thúc câu."""
    idxs: list[int] = []
    expect = True       # đầu đoạn là đầu câu
    pending_end = False  # vừa gặp . ! ? — chờ khoảng trắng để xác nhận hết câu
    for i, ch in enumerate(text):
        if ch.isspace():
            if pending_end:
                expect = True
                pending_end = False
            continue
        if expect and ch.isalpha():
            idxs.append(i)
            expect = False
            pending_end = False
        elif ch in _SENTENCE_END:
            pending_end = True
        else:
            pending_end = False
    return idxs


def _fix_paragraph(para) -> None:
    """Viết hoa chữ cái đầu mỗi câu; map vị trí theo para.text rồi sửa trong run
    để giữ nguyên định dạng. Dùng cùng quy tắc ranh giới câu với check()."""
    text = para.text
    targets = {i for i in _sentence_initial_indices(text) if text[i].islower()}
    if not targets:
        return
    pos = 0
    for run in para.runs:
        rt = run.text
        if not rt:
            continue
        n = len(rt)
        chunk = None
        for ti in targets:
            if pos <= ti < pos + n:
                if chunk is None:
                    chunk = list(rt)
                k = ti - pos
                chunk[k] = chunk[k].upper()
        if chunk is not None:
            run.text = "".join(chunk)
        pos += n


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
