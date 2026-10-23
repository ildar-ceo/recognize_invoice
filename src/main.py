"""Точка входа: FastAPI-приложение, статика и шаблоны."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .pages import router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Распознавание документов")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)