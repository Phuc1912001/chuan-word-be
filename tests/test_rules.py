"""Test rule engine — không cần DB, chỉ phân tích file .docx tạm.

Chạy: pip install -r requirements.txt -r requirements-dev.txt && pytest
"""

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.rules.presets import get_preset
from app.services.analyzer import analyze_file


def _set_margins(section, top, bottom, left, right):
    section.top_margin = Cm(top)
    section.bottom_margin = Cm(bottom)
    section.left_margin = Cm(left)
    section.right_margin = Cm(right)


def _make_bad_doc(path: str) -> None:
    doc = Document()
    # khổ giấy mặc định = Letter (sai A4); lề sai
    _set_margins(doc.sections[0], top=1.0, bottom=1.0, left=1.0, right=1.0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT     # chưa căn đều
    run = p.add_run("Xin chào")
    run.font.name = "Arial"   # phông sai
    run.font.size = Pt(20)    # cỡ sai
    # không thụt đầu dòng
    doc.save(path)


def _make_good_doc(path: str) -> None:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)      # A4
    sec.page_height = Cm(29.7)
    _set_margins(sec, top=2.0, bottom=2.0, left=3.0, right=2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal.paragraph_format.line_spacing = 1.5
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.0)
    run = p.add_run("Xin chào")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    doc.save(path)


def test_detects_format_issues(tmp_path):
    path = tmp_path / "bad.docx"
    _make_bad_doc(str(path))

    report = analyze_file(str(path), get_preset())
    codes = set(report.by_rule)

    for expected in {"FONT", "FONT_SIZE", "MARGIN", "PAGE_SIZE", "ALIGNMENT", "INDENT"}:
        assert expected in codes, f"thiếu rule {expected}; có: {codes}"
    assert report.total_errors >= 6
    assert report.score < 100


def test_clean_doc_has_no_issues(tmp_path):
    path = tmp_path / "good.docx"
    _make_good_doc(str(path))

    report = analyze_file(str(path), get_preset())

    assert report.total_errors == 0, f"không nên có lỗi nhưng có: {report.by_rule}"
    assert report.score == 100.0


def test_error_shape_matches_frontend(tmp_path):
    """Mỗi issue phải map được sang {id, type, message, suggestion, page}."""
    path = tmp_path / "bad.docx"
    _make_bad_doc(str(path))

    report = analyze_file(str(path), get_preset())
    issue = report.issues[0]

    assert issue.rule_code
    assert issue.message
    assert issue.suggestion  # rule định dạng luôn kèm gợi ý sửa


def test_capitalization_detects_and_fixes(tmp_path):
    from app.rules.capitalization import CapitalizationRule
    from app.services.docx_parser import load_docx

    path = tmp_path / "cap.docx"
    doc = Document()
    doc.add_paragraph("xin chào. hôm nay trời đẹp.")  # 2 câu chưa viết hoa
    doc.save(str(path))

    pd = load_docx(str(path))
    rule = CapitalizationRule()
    spec = get_preset()

    assert rule.check(pd, spec), "phải phát hiện lỗi viết hoa đầu câu"

    rule.fix(pd, spec)
    assert rule.check(pd, spec) == [], "sau fix không còn lỗi viết hoa đầu câu"
    assert pd.paragraphs[0].text.startswith("Xin chào. Hôm nay")
