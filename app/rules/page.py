"""Rule kiểm tra khổ giấy & hướng trang (A4 dọc)."""

from __future__ import annotations

from app.rules.types import Issue, ParsedDoc, TemplateSpec


class PageSizeRule:
    code = "PAGE_SIZE"
    name = "Khổ giấy & hướng trang"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        from docx.enum.section import WD_ORIENT

        ps = spec.page
        issues: list[Issue] = []
        for section in doc.sections:
            w, h = section.page_width, section.page_height
            if w is not None and h is not None:
                short_mm, long_mm = sorted([w.mm, h.mm])
                exp_short, exp_long = sorted([ps.width_mm, ps.height_mm])
                if (abs(short_mm - exp_short) > ps.tolerance_mm
                        or abs(long_mm - exp_long) > ps.tolerance_mm):
                    issues.append(Issue(
                        rule_code=self.code,
                        message=(
                            f"Khổ giấy {w.mm:.0f}×{h.mm:.0f}mm không phải A4 "
                            f"({ps.width_mm:.0f}×{ps.height_mm:.0f}mm)"
                        ),
                        suggestion="Đặt khổ giấy A4 (210×297mm)",
                    ))

            if ps.orientation == "portrait" and section.orientation == WD_ORIENT.LANDSCAPE:
                issues.append(Issue(
                    rule_code=self.code,
                    message="Trang đang nằm ngang (landscape)",
                    suggestion="Đặt hướng trang dọc (portrait)",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.enum.section import WD_ORIENT
        from docx.shared import Mm

        ps = spec.page
        short_mm, long_mm = sorted([ps.width_mm, ps.height_mm])
        for section in doc.sections:
            if ps.orientation == "portrait":
                section.orientation = WD_ORIENT.PORTRAIT
                section.page_width = Mm(short_mm)
                section.page_height = Mm(long_mm)
            else:
                section.orientation = WD_ORIENT.LANDSCAPE
                section.page_width = Mm(long_mm)
                section.page_height = Mm(short_mm)
