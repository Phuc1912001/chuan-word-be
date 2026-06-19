FROM python:3.11-slim

# LibreOffice cho bước xem trước (docx -> pdf)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-infra.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-infra.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
