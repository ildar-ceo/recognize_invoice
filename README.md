# Система распознавания электронных документов

Веб-интерфейс (FastAPI + Jinja2) для распознавания сканов/фото документов (счета-фактуры, накладные и т.п.) через LLM. MVP без интеграции с 1С.

## Запуск

```bash
pip install -r src/requirements.txt
cp .env.example .env      # заполнить MODEL_NAME / MODEL_KEY / MODEL_URL
python -m src.main        # http://127.0.0.1:8000
```

Если настройки LLM не заполнены — работает демо-режим с заглушкой (фиктивный результат без вызова API).

## Сборка Docker-образа

```bash
chmod +x build.sh
./build.sh docker    # собрать образ doc-recognition:latest
./build.sh help      # справка по командам
./build.sh           # без команды — тоже выводит справку
```

Образ запускается командой:

```bash
docker run --rm -p 8000:8000 --env-file .env doc-recognition:latest
```

## Структура

Смотрите [docs/task.md](docs/task.md).

## Настройки

| Переменная | Назначение |
|---|---|
| `MODEL_NAME` | название модели |
| `MODEL_KEY` | API-ключ |
| `MODEL_URL` | URL API |

Настройки можно менять на странице `/settings` — они сохраняются в `.env` (файл не коммитится).