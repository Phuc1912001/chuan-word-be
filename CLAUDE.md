# chuan-word-be — Backend

FastAPI service phân tích & chuẩn hóa file `.docx`. Giai đoạn hiện tại mới có endpoint upload + schema kết quả phân tích; đang tiến tới kiến trúc async (Celery/Redis/S3) — **kiến trúc đầy đủ ở [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)**.

## Stack

- **Python 3.11+**, FastAPI, Uvicorn
- **SQLAlchemy 2.0** + Alembic, **PostgreSQL** (`psycopg2-binary`)
- **python-docx** + **lxml** — đọc/sửa OOXML
- Pydantic v2 / pydantic-settings cho config

## Setup (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # rồi điền SQLALCHEMY_DATABASE_URL
```

## Lệnh thường dùng

```powershell
uvicorn app.main:app --reload          # chạy dev server (http://127.0.0.1:8000, docs tại /docs)
alembic revision --autogenerate -m "msg"   # tạo migration từ thay đổi model
alembic upgrade head                   # áp dụng migration
alembic downgrade -1                    # lùi 1 bước
pytest                                  # chạy test (khi đã có)

# GĐ0 — async job qua Celery + Redis:
celery -A app.worker.celery_app:celery_app worker --loglevel=info --pool=solo   # worker (Windows: --pool=solo)
# Dev không có Redis: đặt CELERY_TASK_ALWAYS_EAGER=true để task chạy inline.
# Hoặc dùng Docker: docker compose up --build  (api + worker + redis)
```

**Hai luồng phân tích cùng tồn tại:**
- Sync (đơn giản, hiện FE đang dùng): `POST /analyze/{id}`, `/fix`, `/preview`.
- Async (GĐ0, scale): `POST /jobs {file_id}` → 202 + `job_id`; worker xử lý nền; poll `GET /jobs/{id}`.

File lưu qua `app/services/storage.py` (local mặc định, S3 nếu `STORAGE_BACKEND=s3`).

> Sau khi thêm/sửa model trong `app/models/`, nhớ import nó ở nơi Alembic `env.py` nhìn thấy `Base.metadata`, rồi `revision --autogenerate`.

## Cấu trúc

```
app/
├─ main.py            # FastAPI app + include routers
├─ api/
│  ├─ deps.py         # dependencies (vd get_db)
│  └─ endpoints/      # router theo domain (upload.py, book.py...)
├─ core/config.py     # Settings (đọc .env qua pydantic-settings)
├─ db/
│  ├─ base.py         # Base = declarative_base()
│  └─ session.py      # engine + SessionLocal + get_db()
├─ models/            # SQLAlchemy models (1 file / bảng)
└─ schemas/           # Pydantic schemas (request/response)
alembic/              # migrations
```

## Quy ước

- **Model**: 1 file / bảng trong `app/models/`, kế thừa `Base` từ `app.db.base`. Cột `rule_code` dùng các mã định dạng: `FONT`, `MARGIN_LEFT`, `QUOC_HIEU`, ...
- **Endpoint trả về Pydantic schema**, không trả thẳng object SQLAlchemy (endpoint `upload` hiện tại đang trả thẳng object — cần refactor).
- **Không xử lý nặng (đọc docx + gọi LLM) trong request HTTP** — kiến trúc mục tiêu đẩy vào worker nền; tránh thêm logic blocking vào endpoint.
- **Output lỗi ngữ nghĩa** phải khớp shape FE đang dùng: `{id, type, message, suggestion, page}`.
- File upload mục tiêu lưu **S3**, không lưu `uploads/` local (code hiện tại lưu local — sẽ đổi).
- Biến môi trường: chỉ thêm vào `core/config.py` (`Settings`) và cập nhật `.env.example`.

## Rule engine

Mỗi quy tắc định dạng là một class theo interface chung với `check()` (phát hiện lỗi) và `fix()` (auto-fix), chạy trên `TemplateSpec` (preset hoặc custom từ file mẫu). Dùng `/new-rule` để scaffold.

**Đặc tả quy chuẩn Nghị định 30 (nguồn chân lý cho rule + preset): [../../docs/quy-chuan-nd30.md](../../docs/quy-chuan-nd30.md)** — bảng mapping yêu cầu → `rule_code` → trạng thái, các rule chưa làm (`PAGE_SIZE`, `ALIGNMENT`, `INDENT`, `PAGE_NUMBER`, `CAPITALIZATION`), và điểm vênh giãn dòng cần chốt. Đã làm: `FONT`, `FONT_SIZE`, `MARGIN`, `LINE_SPACING`.
