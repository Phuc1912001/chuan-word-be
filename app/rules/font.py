"""Rule kiểm tra phông chữ và cỡ chữ."""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec


def _normal_font(doc: ParsedDoc):
    """Trả về (name, size_pt) của style 'Normal', hoặc (None, None) nếu không xác định."""
    try:
        font = doc.styles["Normal"].font
    except KeyError:
        return None, None
    size_pt = font.size.pt if font.size is not None else None
    return font.name, size_pt


class FontRule:
    code = "FONT"
    name = "Phông chữ"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        target = spec.font.name
        issues: list[Issue] = []

        normal_name, _ = _normal_font(doc)
        if normal_name and normal_name != target:
            issues.append(Issue(
                rule_code=self.code,
                message=f"Phông chữ mặc định '{normal_name}' không đúng chuẩn '{target}'",
                suggestion=f"Đổi phông mặc định sang {target}",
            ))

        seen: set[int] = set()
        for i, para in enumerate(doc.paragraphs):
            for run in para.runs:
                name = run.font.name
                if name and name != target and i not in seen:
                    seen.add(i)
                    issues.append(Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: phông '{name}' không đúng chuẩn '{target}'",
                        suggestion=f"Đổi sang {target}",
                    ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        target = spec.font.name
        try:
            doc.styles["Normal"].font.name = target
        except KeyError:
            pass
        for para in doc.paragraphs:
            for run in para.runs:
                if run.font.name:
                    run.font.name = target


class FontSizeRule:
    code = "FONT_SIZE"
    name = "Cỡ chữ"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        lo, hi = spec.font.size_pt_min, spec.font.size_pt_max
        issues: list[Issue] = []
        seen: set[int] = set()
        for i, para in enumerate(doc.paragraphs):
            for run in para.runs:
                size = run.font.size
                if size is None:
                    continue
                pt = size.pt
                if (pt < lo or pt > hi) and i not in seen:
                    seen.add(i)
                    issues.append(Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: cỡ chữ {pt:g}pt ngoài khoảng {lo:g}–{hi:g}pt",
                        suggestion=f"Đặt cỡ chữ {spec.font.fix_size_pt:g}pt",
                    ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.shared import Pt

        lo, hi = spec.font.size_pt_min, spec.font.size_pt_max
        for para in doc.paragraphs:
            for run in para.runs:
                size = run.font.size
                if size is not None and (size.pt < lo or size.pt > hi):
                    run.font.size = Pt(spec.font.fix_size_pt)
