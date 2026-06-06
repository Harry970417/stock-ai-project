FROM python:3.12-slim

WORKDIR /app

# 安裝系統依賴（lxml 需要 libxml2）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# watchlist.json 存放於可掛載的 /app/data 目錄
RUN mkdir -p /app/data
ENV WATCHLIST_DIR=/app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
