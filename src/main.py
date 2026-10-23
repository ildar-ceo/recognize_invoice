"""Точка входа: FastAPI-приложение, статика и шаблоны."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .pages import router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Распознавание документов")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    # при DEBUG=1 uvicorn следит за изменением файлов и перезапускает процесс
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )