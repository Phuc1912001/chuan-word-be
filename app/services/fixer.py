"""Auto-fix: áp các fix() của rule engine lên file .docx và lưu bản đã chuẩn hóa.

Chỉ sửa ĐỊNH DẠNG, không đổi nội dung văn bản. Hàm thuần (không đụng DB).
"""

from __future__ import annotations

from docx import Document

from app.rules.registry import default_rules
from app.rules.types import ParsedDoc, TemplateSpec


def fix_file(src_path: str, spec: TemplateSpec, out_path: str, rules=None) -> str:
    """Đọc `src_path`, áp tất cả rule.fix() theo `spec`, lưu ra `out_path`. Trả về out_path."""
    rules = rules if rules is not None else default_rules()
    document = Document(src_path)
    doc = ParsedDoc(document=document)
    for rule in rules:
        rule.fix(doc, spec)
    document.save(out_path)
    return out_path
