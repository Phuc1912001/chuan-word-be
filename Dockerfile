FROM python:3.11-slim

# Preview render .docx ở phía FE (docx-preview) → KHÔNG cần LibreOffice.
# Chỉ thêm libreoffice-writer nếu sau này bật lại xuất PDF server-side.

WORKDIR /app

COPY requirements.txt requirements-infra.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-infra.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
