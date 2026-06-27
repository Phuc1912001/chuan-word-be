"""Phân loại đoạn văn theo thành phần văn bản hành chính (Nghị định 30).

Mục tiêu: gán cho mỗi đoạn THÂN TÀI LIỆU một nhãn (Quốc hiệu / Tiêu ngữ /
Địa danh-ngày / Tên loại VB / Nội dung / Họ tên ký / Khác) để các rule áp cỡ
chữ, kiểu chữ và thụt đầu dòng đúng từng phần (bảng III + mục I/IV ảnh chuẩn).

NGUYÊN TẮC: BẢO THỦ. Chỉ gán nhãn đặc biệt khi có tín hiệu MẠNH (khớp văn bản
cố định, hoặc nhiều dấu hiệu đồng thời). Mọi trường hợp còn lại → 'noi_dung'
(cỡ 13–14, an toàn) hoặc 'khac'. Nhãn sai dễ gây sửa nhầm nên thà bỏ sót.

Map nhãn theo VỊ TRÍ (không dùng id của proxy lxml vì id bị tái sử dụng sau GC
→ tra cứu sai). `classify_body`/`classify_all` trả list[(paragraph, nhãn)] đúng
thứ tự duyệt; rule chỉ cần lặp đúng thứ tự đó.
"""

from __future__ import annotations

import re
import unicodedata

from app.rules.docx_iter import (
    iter_body_with_flag,
    iter_header_footer_paragraphs,
    iter_top_level_paragraphs,
)
from app.rules.types import (
    COMP_DIA_DANH_NGAY,
    COMP_HO_TEN_KY,
    COMP_KHAC,
    COMP_NOI_DUNG,
    COMP_QUOC_HIEU,
    COMP_TEN_LOAI_VB,
    COMP_TIEU_NGU,
)

# Các loại văn bản hành chính phổ biến (đã bỏ dấu, in hoa) — dấu hiệu Tên loại VB.
_DOC_TYPES = {
    "QUYET DINH", "NGHI DINH", "NGHI QUYET", "THONG BAO", "THONG TU",
    "CONG VAN", "TO TRINH", "BAO CAO", "KE HOACH", "CHI THI", "QUY DINH",
    "QUY CHE", "HUONG DAN", "BIEN BAN", "GIAY MOI", "GIAY BAO", "DON",
    "CONG DIEN", "PHUONG AN", "DE AN", "THONG CAO", "LENH", "SAC LENH",
}

_DATE_RE = re.compile(r"ng[àa]y\s+\d{1,2}\s+th[áa]ng\s+\d{1,2}\s+n[ăa]m\s+\d{2,4}", re.I)


def _strip_accents(s: str) -> str:
    # Đ/đ là CHỮ CÁI Latin riêng, NFD KHÔNG tách dấu → phải thay tay trước.
    s = s.replace("Đ", "D").replace("đ", "d")
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _norm(text: str) -> str:
    """Bỏ dấu + in hoa + gộp khoảng trắng → so khớp văn bản cố định bền vững."""
    return re.sub(r"\s+", " ", _strip_accents(text)).strip().upper()


def _is_centered(para) -> bool:
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
        return True
    try:
        return para.style.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    except Exception:
        return False


def _is_mostly_bold(para) -> bool:
    runs = [r for r in para.runs if r.text.strip()]
    return bool(runs) and all(r.bold for r in runs)


def _looks_like_person_name(text: str) -> bool:
    """2–5 từ, mỗi từ viết hoa chữ đầu, không kết thúc bằng dấu câu → giống tên người."""
    t = text.strip()
    if not t or t[-1] in ".!?:;,":
        return False
    words = t.split()
    if not (2 <= len(words) <= 5):
        return False
    return all(w[:1].isupper() for w in words if w[:1].isalpha())


def _classify_list(paras: list) -> list[str]:
    """Gán nhãn cho list đoạn THÂN tài liệu, theo đúng thứ tự."""
    n = len(paras)
    out: list[str] = []
    seen_quoc_hieu = seen_tieu_ngu = seen_ten_loai = False

    for i, para in enumerate(paras):
        text = para.text.strip()
        if not text:
            out.append(COMP_KHAC)
            continue

        norm = _norm(text)
        is_upper = text == text.upper() and any(c.isalpha() for c in text)
        word_count = len(text.split())

        # 1) Quốc hiệu — khớp văn bản cố định (rất mạnh)
        if not seen_quoc_hieu and "CONG HOA XA HOI CHU NGHIA VIET NAM" in norm:
            out.append(COMP_QUOC_HIEU)
            seen_quoc_hieu = True
            continue

        # 2) Tiêu ngữ — "Độc lập - Tự do - Hạnh phúc"
        if not seen_tieu_ngu and all(k in norm for k in ("DOC LAP", "TU DO", "HANH PHUC")):
            out.append(COMP_TIEU_NGU)
            seen_tieu_ngu = True
            continue

        # 3) Địa danh, ngày tháng — "..., ngày ... tháng ... năm ..."
        if _DATE_RE.search(text):
            out.append(COMP_DIA_DANH_NGAY)
            continue

        # 4) Tên loại văn bản — in hoa, ngắn, nửa đầu tài liệu
        #    (khớp danh sách loại VB đủ mạnh; nếu không thì cần căn giữa + đậm).
        in_first_half = i < max(8, n // 2)
        if not seen_ten_loai and in_first_half and is_upper and word_count <= 8:
            hit_keyword = any(norm == kw or norm.startswith(kw + " ") for kw in _DOC_TYPES)
            if hit_keyword or (_is_centered(para) and _is_mostly_bold(para)):
                out.append(COMP_TEN_LOAI_VB)
                seen_ten_loai = True
                continue

        # 5) Họ tên người ký — cuối tài liệu, giống tên người, đậm
        in_last_quarter = i >= n - max(1, n // 4)
        if in_last_quarter and _is_mostly_bold(para) and _looks_like_person_name(text):
            out.append(COMP_HO_TEN_KY)
            continue

        # 6) Mặc định. Đoạn CĂN GIỮA là tiêu đề/phụ đề, KHÔNG phải nội dung body
        #    → 'khac' (không thụt đầu dòng, không giãn đoạn). Body chỉ tính đoạn
        #    nhiều chữ, không căn giữa.
        if _is_centered(para):
            out.append(COMP_KHAC)
        else:
            out.append(COMP_NOI_DUNG if word_count >= 5 else COMP_KHAC)

    return out


def classify_top_level(doc) -> list[tuple]:
    """List (paragraph, nhãn) cho đoạn CẤP THÂN (không vào bảng).

    Các thành phần cấu trúc (Quốc hiệu/Tiêu ngữ/Tên loại VB/chữ ký) luôn ở cấp
    thân, không nằm trong bảng → chỉ phân loại ở đây để tránh nhận nhầm nội dung
    ô bảng. Dùng cho rule bố cục (thụt dòng, giãn đoạn) và kiểu chữ thành phần."""
    paras = iter_top_level_paragraphs(doc)
    return list(zip(paras, _classify_list(paras)))


def classify_all(doc) -> list[tuple]:
    """List (paragraph, nhãn) cho MỌI đoạn theo thứ tự iter_all_paragraphs:
    đoạn cấp thân (đã phân loại) + đoạn trong bảng ('noi_dung') + header/footer
    ('noi_dung'). Dùng cho rule ký tự (cỡ chữ) cần phủ cả bảng."""
    top_labels = _classify_list(iter_top_level_paragraphs(doc))
    result: list[tuple] = []
    ti = 0
    for para, in_table in iter_body_with_flag(doc):
        if in_table:
            result.append((para, COMP_NOI_DUNG))
        else:
            result.append((para, top_labels[ti]))
            ti += 1
    for para in iter_header_footer_paragraphs(doc):
        result.append((para, COMP_NOI_DUNG))
    return result
