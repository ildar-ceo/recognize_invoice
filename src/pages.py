"""Маршруты страниц: загрузка, предпросмотр, настройки + API распознавания."""
import json
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import save_settings, settings
from .recognition import recognize
from .schemas import Document

BASE_DIR = Path(__file__).resolve().parent

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Результат последнего распознавания (MVP-состояние в памяти)
_last_result: Document | None = None


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.post("/api/recognize")
async def api_recognize(file: UploadFile = File(...)):
    global _last_result
    image = await file.read()
    _last_result = await recognize(image, file.content_type or "image/png")
    return {"ok": True, "doc": json.loads(_last_result.model_dump_json())}


@router.get("/preview", response_class=HTMLResponse)
async def preview(request: Request):
    if _last_result is None:
        return RedirectResponse("/", status_code=302)
    doc_json = json.dumps(json.loads(_last_result.model_dump_json()),
                          ensure_ascii=False, indent=2)
    return templates.TemplateResponse(request, "preview.html",
                                      {"doc": _last_result, "doc_json": doc_json})


@router.post("/preview/confirm")
async def preview_confirm():
    """Подтверждение пользователем (этап 6 — отправка в 1С — после MVP)."""
    return RedirectResponse("/", status_code=302)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html",
                                      {"s": settings, "saved": False})


@router.post("/settings", response_class=HTMLResponse)
async def settings_save(request: Request):
    form = await request.form()
    save_settings(
        str(form.get("model_name", "")),
        str(form.get("model_key", "")),
        str(form.get("model_url", "")),
    )
    return templates.TemplateResponse(request, "settings.html",
                                      {"s": settings, "saved": True})