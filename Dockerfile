FROM python:3.11-slim
ENV PYTHONUNBUFFERED True
WORKDIR /app

# 先に requirements.txt だけコピーしてインストールする
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# その後にソースコードをコピーする
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]