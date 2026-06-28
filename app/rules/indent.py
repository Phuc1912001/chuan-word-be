# """Rule thụt đầu dòng (INDENT).

# Bản cũ bắt MỌI đoạn không căn giữa phải thụt → báo lỗi oan tiêu đề, quốc hiệu,
# dòng ký, danh sách... ("lỗi tùm lum"). Bản mới CHỈ áp cho đoạn được classifier
# gắn nhãn 'noi_dung' (thành phần có first_line_indent=True), bỏ qua:
# - đoạn căn giữa (tiêu đề),
# - đoạn có thụt âm (hanging indent — danh sách),
# - nội dung trong bảng/header/footer (không duyệt ở đây).
# """

# from __future__ import annotations

# from app.rules.classifier import classify_top_level
# from app.rules.types import Issue, ParsedDoc, TemplateSpec

# _EPS = 0.01


# def _first_line_cm(para) -> float:
#     fli = para.paragraph_format.first_line_indent
#     return fli.cm if fli is not None else 0.0


# def _is_centered(para) -> bool:
#     from docx.enum.text import WD_ALIGN_PARAGRAPH

#     return para.alignment == WD_ALIGN_PARAGRAPH.CENTER


# class IndentRule:
#     code = "INDENT"
#     name = "Thụt đầu dòng"

#     def _targets(self, doc, spec):
#         for i, (para, label) in enumerate(classify_top_level(doc)):
#             if not para.text.strip() or _is_centered(para):
#                 continue
#             comp = spec.component(label)
#             if not comp.first_line_indent:
#                 continue
#             yield i, para

#     def check(self, doc: ParsedDoc, spec: TemplateSpec) -> list[Issue]:
#         lo, hi = spec.indent.min_cm, spec.indent.max_cm
#         issues: list[Issue] = []
#         for i, para in self._targets(doc, spec):
#             cm = _first_line_cm(para)
#             if -_EPS <= cm < lo - _EPS:  # bỏ qua thụt âm (hanging)
#                 issues.append(Issue(
#                     rule_code=self.code,
#                     paragraph_index=i,
#                     message=f"Đoạn {i + 1}: chưa thụt đầu dòng (cần {lo:g}–{hi:g}cm)",
#                     suggestion=f"Thụt đầu dòng {spec.indent.fix_to_cm:g}cm",
#                 ))
#         return issues

#     def fix(self, doc: ParsedDoc, spec: TemplateSpec) -> None:
#         from docx.shared import Cm

#         lo = spec.indent.min_cm
#         for _i, para in self._targets(doc, spec):
#             cm = _first_line_cm(para)
#             if -_EPS <= cm < lo - _EPS:
#                 para.paragraph_format.first_line_indent = Cm(spec.indent.fix_to_cm)
