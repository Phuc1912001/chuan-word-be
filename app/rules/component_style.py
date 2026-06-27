"""Rule kiểu chữ theo thành phần (COMPONENT_STYLE) — đậm/nghiêng theo bảng III.

Chỉ áp cho các thành phần ĐƯỢC NHẬN DIỆN MẠNH (Quốc hiệu, Tiêu ngữ, Địa danh-
ngày, Tên loại VB, Họ tên ký) — nơi spec quy định bold/italic rõ ràng. Nội dung
thường và đoạn 'khác' không bị đụng tới (bold=italic=None) nên rủi ro sửa nhầm
thấp. Không đổi cỡ chữ ở đây (đã có FONT_SIZE) và không đổi nội dung (in hoa).
"""

from __future__ import annotations

from app.rules.classifier import classify_top_level
from app.rules.types import COMPONENT_LABELS, Issue, ParsedDoc, TemplateSpec


def _text_runs(para):
    return [r for r in para.runs if r.text.strip()]


class ComponentStyleRule:
    code = "COMPONENT_STYLE"
    name = "Kiểu chữ theo thành phần"

    def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
        issues: list[Issue] = []
        for i, (para, label) in enumerate(classify_top_level(doc)):
            runs = _text_runs(para)
            if not runs:
                continue
            comp = spec.component(label)
            problems: list[str] = []
            if comp.bold is not None and not all(bool(r.bold) == comp.bold for r in runs):
                problems.append("đậm" if comp.bold else "không đậm")
            if comp.italic is not None and not all(bool(r.italic) == comp.italic for r in runs):
                problems.append("nghiêng" if comp.italic else "không nghiêng")
            if problems:
                ten = COMPONENT_LABELS.get(label, "Văn bản")
                issues.append(Issue(
                    rule_code=self.code,
                    paragraph_index=i,
                    message=f"Đoạn {i + 1} ({ten}): kiểu chữ chưa đúng",
                    suggestion=f"Đặt {ten} thành: {', '.join(problems)}",
                ))
        return issues

    def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
        for para, label in classify_top_level(doc):
            runs = _text_runs(para)
            if not runs:
                continue
            comp = spec.component(label)
            for run in runs:
                if comp.bold is not None:
                    run.bold = comp.bold
                if comp.italic is not None:
                    run.italic = comp.italic
