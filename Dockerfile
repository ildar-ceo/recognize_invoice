# Сборка образа системы распознавания электронных документов
FROM python:3.12-slim

# Не выводить буферизацию, чтобы логи сразу были видны
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Сначала только зависимости — чтобы слой кешировался
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY src/ ./src/

EXPOSE 8000

# Приложение должно слушать 0.0.0.0, а не 127.0.0.1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]