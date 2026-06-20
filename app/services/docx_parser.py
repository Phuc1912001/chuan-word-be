"""Đọc file .docx thành ParsedDoc cho rule engine."""

from __future__ import annotations

from docx import Document

from app.rules.types import ParsedDoc


def load_docx(path: str) -> ParsedDoc:
    """Mở file .docx tại `path`. Ném docx.opc.exceptions.PackageNotFoundError nếu file hỏng/không phải .docx."""
    return ParsedDoc(document=Document(path))
