"""Rule kiểm tra lề trang (margin) theo từng section."""

from __future__ import annotations

from app.rules.types import Issue, MarginRange, ParsedDoc, TemplateSpec

_LABELS = {"top": "trên", "bottom": "dưới", "left": "trái", "right": "phải"}


class MarginRule:
    code = "MARGIN"
    name = "Lề trang"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for section in doc.sections:
            values = {
                "top": section.top_margin,
                "bottom": section.bottom_margin,
                "left": section.left_margin,
                "right": section.right_margin,
            }
            for key, length in values.items():
                if length is None:
                    continue
                cm = length.cm
                rng: MarginRange = getattr(spec.margins, key)
                # dung sai 0.01cm để tránh báo sai do làm tròn
                if cm < rng.min_cm - 0.01 or cm > rng.max_cm + 0.01:
                    issues.append(Issue(
                        rule_code=self.code,
                        message=(
                            f"Lề {_LABELS[key]} {cm:.2f}cm ngoài khoảng "
                            f"{rng.min_cm:g}–{rng.max_cm:g}cm"
                        ),
                        suggestion=f"Đặt lề {_LABELS[key]} {rng.fix_to_cm:g}cm",
                    ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        from docx.shared import Cm

        for section in doc.sections:
            section.top_margin = Cm(spec.margins.top.fix_to_cm)
            section.bottom_margin = Cm(spec.margins.bottom.fix_to_cm)
            section.left_margin = Cm(spec.margins.left.fix_to_cm)
            section.right_margin = Cm(spec.margins.right.fix_to_cm)
