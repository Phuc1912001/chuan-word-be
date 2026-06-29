"""Rule chính tả tiếng Việt dựa trên một bộ sửa lỗi thủ công, nhẹ và an toàn.

Mục tiêu là phát hiện những lỗi rất phổ biến như "khong" → "không",
"duoc" → "được". Rule này không cố gắng sửa toàn bộ văn bản hay dùng
phân tích ngữ nghĩa; chỉ áp dụng cho các từ có trong danh sách mapping cố định.
"""

from __future__ import annotations

import re

from app.rules.types import Issue, ParsedDoc, TemplateSpec

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")

# Danh sách lỗi chính tả phổ biến, bỏ qua các trường hợp quá rộng để tránh sửa sai.
TYPO_MAP = {
    "khong": "không",
    "không": "không",
    "duoc": "được",
    "đuoc": "được",
    "thay": "thấy",
    "khac": "khác",
    "nhieu": "nhiều",
    "nho": "nhỏ",
    "nghia": "nghĩa",
    "tien": "tiến",
    "quyen": "quyền",
}


def _replace_tokens(text: str) -> tuple[str, int]:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        normalized = token.lower()
        replacement = TYPO_MAP.get(normalized)
        if replacement is None:
            return token
        if token[:1].isupper():
            return replacement.capitalize()
        return replacement

    new_text, count = _WORD_RE.subn(repl, text)
    return new_text, count


class SpellingRule:
    code = "SPELLING"
    name = "Chính tả tiếng Việt"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            if not text.strip():
                continue
            _, count = _replace_tokens(text)
            if count:
                issues.append(
                    Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: có {count} từ có thể viết sai chính tả",
                        suggestion="Sửa các từ sai chính tả theo chuẩn tiếng Việt",
                    )
                )
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            fixed_text, _ = _replace_tokens(para.text)
            if fixed_text != para.text:
                # Cập nhật từng run để giữ định dạng tốt hơn.
                runs = list(para.runs)
                if not runs:
                    para.add_run(fixed_text)
                    continue

                # Xóa toàn bộ run hiện có rồi viết lại text đã sửa.
                for run in runs:
                    run.text = ""
                # Rebuild paragraph text with a single run to avoid partial mismatch.
                if runs:
                    runs[0].text = fixed_text
                else:
                    para.add_run(fixed_text)
