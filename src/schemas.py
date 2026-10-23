"""Pydantic-схемы документа: единый контракт между tools, JSON и UI."""
import re
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

# ---------- нормализация ----------

_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def to_iso_date(value: Optional[Union[str, int]]) -> Optional[str]:
    """16.11.2022 / 12 июня 2008 → 2022-11-16 / 2008-06-12. Неизвестное — как есть."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", s.lower())
    if m and m.group(2) in _MONTHS:
        return f"{m.group(3)}-{_MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return s


def to_decimal(value: Optional[Union[str, int, float, Decimal]]) -> Optional[Decimal]:
    """780,00 / «5 240,00» → Decimal. Нераспознанное → None (не угадывать)."""
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).replace("\xa0", "").replace(" ", "").replace("руб.", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


# ---------- модели ----------

class DocType(str, Enum):
    TORG12 = "torg12"        # товарная накладная (ТОРГ-12)
    INVOICE = "invoice"      # счет-фактура / счет
    ACT = "act"              # акт
    CUSTOM = "custom"        # прочее / не распознано


DOC_TYPE_ALIASES = {
    "товарная накладная": DocType.TORG12,
    "накладная": DocType.TORG12,
    "торг-12": DocType.TORG12,
    "торг12": DocType.TORG12,
    "счет-фактура": DocType.INVOICE,
    "счёт-фактура": DocType.INVOICE,
    "счет": DocType.INVOICE,
    "счёт": DocType.INVOICE,
    "акт": DocType.ACT,
}


def normalize_doc_type(raw: str) -> DocType:
    s = (raw or "").strip().lower()
    if s in {t.value for t in DocType}:
        return DocType(s)
    return DOC_TYPE_ALIASES.get(s, DocType.CUSTOM)


class Header(BaseModel):
    form_code: Optional[str] = None
    number: Optional[str] = None
    date: Optional[str] = None
    consignor: Optional[str] = None       # грузоотправитель
    consignee: Optional[str] = None       # грузополучатель
    supplier: Optional[str] = None        # поставщик
    payer: Optional[str] = None           # плательщик
    basis: Optional[str] = None           # основание
    total_in_words: Optional[str] = None  # сумма прописью

    @field_validator("date", mode="before")
    @classmethod
    def _date(cls, v):
        return to_iso_date(v)


class Row(BaseModel):
    line_no: Optional[int] = None
    name: str
    code: Optional[str] = None
    barcode: Optional[str] = None
    unit: Optional[str] = None
    okei: Optional[str] = None
    qty: Optional[Decimal] = None
    netto: Optional[Decimal] = None
    price: Optional[Decimal] = None
    sum_without_vat: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    vat_sum: Optional[Decimal] = None
    sum_with_vat: Optional[Decimal] = None

    @field_validator("qty", "netto", "price", "sum_without_vat",
                     "vat_rate", "vat_sum", "sum_with_vat", mode="before")
    @classmethod
    def _numbers(cls, v):
        if isinstance(v, str) and "без ндс" in v.lower():
            return None
        return to_decimal(v)


class Totals(BaseModel):
    qty: Optional[Decimal] = None
    netto: Optional[Decimal] = None
    sum_without_vat: Optional[Decimal] = None
    sum_with_vat: Optional[Decimal] = None

    @field_validator("qty", "netto", "sum_without_vat", "sum_with_vat", mode="before")
    @classmethod
    def _numbers(cls, v):
        return to_decimal(v)


class Signature(BaseModel):
    role: str
    position: Optional[str] = None
    fio: Optional[str] = None


class Document(BaseModel):
    doc_type: DocType = DocType.CUSTOM
    header: Header = Field(default_factory=Header)
    rows: list[Row] = Field(default_factory=list)
    totals: Totals = Field(default_factory=Totals)
    signatures: list[Signature] = Field(default_factory=list)