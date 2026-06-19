"""Convert .docx → PDF bằng LibreOffice headless (cho bước xem trước).

Cần cài LibreOffice; có thể override đường dẫn qua biến môi trường SOFFICE_PATH.
GĐ0 sẽ chuyển convert vào worker nền thay vì chạy đồng bộ trong request.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
]


def _find_soffice() -> str:
    env = os.environ.get("SOFFICE_PATH")
    if env and os.path.exists(env):
        return env
    for p in _CANDIDATES:
        if os.path.exists(p):
            return p
    found = shutil.which("soffice") or shutil.which("soffice.exe")
    if found:
        return found
    raise RuntimeError(
        "Không tìm thấy LibreOffice (soffice). Cài LibreOffice hoặc đặt biến môi trường SOFFICE_PATH."
    )


def docx_to_pdf(src_path: str, out_dir: str, timeout: int = 120) -> str:
    """Convert `src_path` (.docx) sang PDF trong `out_dir`. Trả về đường dẫn PDF."""
    soffice = _find_soffice()
    src_path = os.path.abspath(src_path)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # profile riêng cho mỗi lần convert → tránh khoá khi chạy song song.
    # UserInstallation cần URI tuyệt đối hợp lệ (file:///C:/...).
    profile = os.path.join(out_dir, f"_loprofile_{uuid.uuid4().hex}")
    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--nolockcheck",
        "--nodefault",
        f"-env:UserInstallation={Path(profile).as_uri()}",
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        out_dir,
        src_path,
    ]
    pdf_path = os.path.join(out_dir, os.path.splitext(os.path.basename(src_path))[0] + ".pdf")
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
        # soffice.exe trên Windows có thể trả về trước khi ghi xong PDF → poll chờ.
        deadline = time.time() + 30
        while not os.path.exists(pdf_path) and time.time() < deadline:
            time.sleep(0.5)
    finally:
        shutil.rmtree(profile, ignore_errors=True)

    if not os.path.exists(pdf_path):
        err = (proc.stderr or b"").decode(errors="ignore")[:300]
        out = (proc.stdout or b"").decode(errors="ignore")[:300]
        raise RuntimeError(f"Convert PDF thất bại (rc={proc.returncode}): {err} {out}")
    return pdf_path
