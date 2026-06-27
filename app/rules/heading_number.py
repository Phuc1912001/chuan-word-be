"""Rule chuẩn hóa đề mục đánh số (HEADING_NUMBER).

Đề mục dạng "1.Tên mục", "2)Nội dung", "1.2.Chi tiết" cần:
- CÓ đúng một khoảng trắng sau dấu chấm/ngoặc của số thứ tự,
- VIẾT HOA chữ cái đầu của tên mục.
→ "1.tên miền đăng ký" ⇒ "1. Tên miền đăng ký".

CHỈ kích hoạt ở ĐẦU ĐOẠN theo mẫu `số(.số)*[.)]` + chữ cái, nên KHÔNG đụng tới
"GMO-Z.com" (giữa câu) hay "3.14" (sau dấu chấm là chữ SỐ, không phải chữ cái).
Chạy cả trong bảng (đề mục thường nằm trong ô bảng). SỬA NỘI DUNG văn bản.
"""

from __future__ import annotations

import re

from app.rules.docx_iter import iter_all_paragraphs
from app.rules.types import Issue, ParsedDoc, TemplateSpec

# nhóm: (lead spaces)(số thứ tự)(dấu . hoặc ))(khoảng trắng)(ký tự đầu tên mục)
_HEADING_RE = re.compile(r"^(\s*)(\d+(?:\.\d+)*)([.)])( *)(\S)")


def _analyze(text: str):
    """Trả (idx_first, need_space, need_upper) nếu là đề mục cần sửa, else None."""
    m = _HEADING_RE.match(text)
    if not m:
        return None
    lead, num, punct, gap, first = m.groups()
    if not first.isalpha():       # vd '3.14' → bỏ qua
        return None
    need_space = len(gap) != 1
    need_upper = first.islower()
    if not (need_space or need_upper):
        return None
    idx_first = len(lead) + len(num) + len(punct) + len(gap)
    return idx_first, need_space, need_upper, len(gap)


def _run_at(para, gidx):
    pos = 0
    for run in para.runs:
        n = len(run.text)
        if pos <= gidx < pos + n:
            return run, gidx - pos
        pos += n
    return None, 0


def _upper_at(para, gidx) -> None:
    run, k = _run_at(para, gidx)
    if run is not None:
        s = run.text
        run.text = s[:k] + s[k].upper() + s[k + 1:]


def _set_single_space_before(para, gidx, cur_gap) -> None:
    """Đảm bảo đúng 1 khoảng trắng ngay trước ký tự ở gidx (gap hiện tại = cur_gap)."""
    if cur_gap == 0:
        run, k = _run_at(para, gidx)
        if run is not None:
            s = run.text
            run.text = s[:k] + " " + s[k:]
        else:  # gidx ở cuối → nối vào run cuối
            if para.runs:
                para.runs[-1].text += " "
    elif cur_gap > 1:
        # xoá bớt khoảng trắng thừa, để lại 1
        start = gidx - cur_gap
        for _ in range(cur_gap - 1):
            run, k = _run_at(para, start)
            if run is None:
                break
            s = run.text
            run.text = s[:k] + s[k + 1:]


class HeadingNumberRule:
    code = "HEADING_NUMBER"
    name = "Đề mục đánh số"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for i, para in enumerate(iter_all_paragraphs(doc)):
            text = para.text
            if not text.strip():
                continue
            res = _analyze(text)
            if res is None:
                continue
            _, need_space, need_upper, _ = res
            parts = []
            if need_space:
                parts.append("cách 1 khoảng trắng sau số thứ tự")
            if need_upper:
                parts.append("viết hoa chữ đầu")
            issues.append(Issue(
                rule_code=self.code,
                paragraph_index=i,
                message=f"Đoạn {i + 1}: đề mục đánh số chưa chuẩn",
                suggestion="Đề mục cần " + " và ".join(parts),
            ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        for para in iter_all_paragraphs(doc):
            text = para.text
            if not text.strip():
                continue
            res = _analyze(text)
            if res is None:
                continue
            idx_first, need_space, need_upper, cur_gap = res
            # viết hoa trước (giữ index ổn định), rồi mới chỉnh khoảng trắng
            if need_upper:
                _upper_at(para, idx_first)
            if need_space:
                _set_single_space_before(para, idx_first, cur_gap)
