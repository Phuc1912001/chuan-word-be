"""Rule phông chữ (FONT) và cỡ chữ theo thành phần (FONT_SIZE).

Khác bản cũ ở 2 điểm cốt lõi:
- Duyệt MỌI đoạn (thân + bảng + header/footer) qua iter_all_paragraphs.
- FONT_SIZE áp khoảng cỡ chữ THEO THÀNH PHẦN (bảng III) nhờ classifier, và
  fix phủ cả run thừa kế (không chỉ run có cỡ chữ tường minh) + set style Normal.
"""

from __future__ import annotations

from docx.oxml.ns import qn

from app.rules.classifier import classify_all
from app.rules.docx_iter import (
    effective_size_pt,
    iter_all_paragraphs,
    run_font_name,
    set_run_font_name,
)
from app.rules.types import COMP_NOI_DUNG, Issue, ParsedDoc, TemplateSpec

_EPS = 0.01


class FontRule:
    code = "FONT"
    name = "Phông chữ"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        target = spec.font.name
        issues: list[Issue] = []

        try:
            normal_name = doc.styles["Normal"].font.name
        except KeyError:
            normal_name = None
        if normal_name and normal_name != target:
            issues.append(Issue(
                rule_code=self.code,
                message=f"Phông chữ mặc định '{normal_name}' không đúng chuẩn '{target}'",
                suggestion=f"Đổi phông mặc định sang {target}",
            ))

        for i, para in enumerate(iter_all_paragraphs(doc)):
            for run in para.runs:
                if not run.text.strip():
                    continue
                name = run_font_name(run)
                if name and name != target:
                    issues.append(Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: phông '{name}' không đúng chuẩn '{target}'",
                        suggestion=f"Đổi sang {target}",
                    ))
                    break  # mỗi đoạn báo 1 lần
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        target = spec.font.name
        # Style Normal: set đủ 4 thuộc tính rFonts để không bị theme/eastAsia ghi đè.
        try:
            normal = doc.styles["Normal"]
            normal.font.name = target
            rpr = normal.element.get_or_add_rPr()
            rfonts = rpr.get_or_add_rFonts()
            for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rfonts.set(qn(attr), target)
        except KeyError:
            pass

        # Phông đồng nhất ở mọi thành phần → ép toàn bộ run có nội dung.
        for para in iter_all_paragraphs(doc):
            for run in para.runs:
                if run.text.strip():
                    set_run_font_name(run, target)


class FontSizeRule:
    code = "FONT_SIZE"
    name = "Cỡ chữ"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        document = doc.document
        issues: list[Issue] = []
        for i, (para, label) in enumerate(classify_all(doc)):
            comp = spec.component(label)
            lo, hi = comp.size_pt_min, comp.size_pt_max
            for run in para.runs:
                if not run.text.strip():
                    continue
                pt = effective_size_pt(run, para, document)
                if pt is None:
                    continue
                if pt < lo - _EPS or pt > hi + _EPS:
                    issues.append(Issue(
                        rule_code=self.code,
                        paragraph_index=i,
                        message=f"Đoạn {i + 1}: cỡ chữ {pt:g}pt ngoài khoảng {lo:g}–{hi:g}pt",
                        suggestion=f"Đặt cỡ chữ {comp.fix_size_pt:g}pt",
                    ))
                    break
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.shared import Pt

        document = doc.document
        body_fix = spec.component(COMP_NOI_DUNG).fix_size_pt
        try:
            doc.styles["Normal"].font.size = Pt(body_fix)
        except KeyError:
            pass

        for para, label in classify_all(doc):
            comp = spec.component(label)
            lo, hi = comp.size_pt_min, comp.size_pt_max
            for run in para.runs:
                if not run.text.strip():
                    continue
                pt = effective_size_pt(run, para, document)
                if pt is None:
                    pt = body_fix  # sau khi set Normal, run thừa kế sẽ là body_fix
                if pt < lo - _EPS or pt > hi + _EPS:
                    run.font.size = Pt(comp.fix_size_pt)
