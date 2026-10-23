"""Распознавание документов: агент LLM, tools, сборка Document (паттерн Strategy)."""
from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.capabilities import AbstractCapability, Caching
from pydantic_ai.messages import BinaryContent

from .config import settings
from .schemas import Document, DocType, Header, Row, Signature, Totals, normalize_doc_type

# --------------------------------------------------------------------------- #
#  Recorder — накопитель данных документа, куда пишутся вызовы tools           #
# --------------------------------------------------------------------------- #


class Recorder:
    def __init__(self) -> None:
        self.doc_type: DocType | None = None
        self.header: dict = {}
        self.rows: list[dict] = []
        self.totals: dict = {}
        self.signatures: list[dict] = []

    def build(self) -> Document:
        return Document(
            doc_type=self.doc_type or DocType.CUSTOM,
            header=Header(**self.header),
            rows=[Row(**r) for r in self.rows],
            totals=Totals(**self.totals),
            signatures=[Signature(**s) for s in self.signatures],
        )


# --------------------------------------------------------------------------- #
#  Tools (строго типизированные)                                               #
# --------------------------------------------------------------------------- #


def set_doc_type(ctx: RunContext[Recorder], doc_type: str) -> str:
    """Определить тип документа (первый прогон)."""
    ctx.deps.doc_type = normalize_doc_type(doc_type)
    return f"Тип: {ctx.deps.doc_type.value}"


def set_header(ctx: RunContext[Recorder], field: str, value: str | None) -> str:
    """Заполнить поле шапки. Закрытое/нечитаемое поле передавать null."""
    ctx.deps.header[field] = value
    return f"{field} = {value}"


def add_row(
    ctx: RunContext[Recorder],
    name: str,
    line_no: int | None = None,
    code: str | None = None,
    barcode: str | None = None,
    unit: str | None = None,
    okei: str | None = None,
    qty: str | None = None,
    netto: str | None = None,
    price: str | None = None,
    sum_without_vat: str | None = None,
    vat_rate: str | None = None,
    vat_sum: str | None = None,
    sum_with_vat: str | None = None,
) -> str:
    """Добавить строку товарной позиции. Закрытые поля передавать null."""
    row: dict = {"name": name}
    for key, value in (("line_no", line_no), ("code", code), ("barcode", barcode),
                       ("unit", unit), ("okei", okei), ("qty", qty), ("netto", netto),
                       ("price", price), ("sum_without_vat", sum_without_vat),
                       ("vat_rate", vat_rate), ("vat_sum", vat_sum),
                       ("sum_with_vat", sum_with_vat)):
        if value is not None:
            row[key] = value
    ctx.deps.rows.append(row)
    return f"Добавлена строка: {name}"


def set_total(ctx: RunContext[Recorder], field: str, value: str | None) -> str:
    """Заполнить итог: qty, netto, sum_without_vat, sum_with_vat."""
    ctx.deps.totals[field] = value
    return f"{field} = {value}"


def set_signature(
    ctx: RunContext[Recorder],
    role: str,
    fio: str | None = None,
    position: str | None = None,
) -> str:
    """Сохранить подпись: роль, фио, должность."""
    ctx.deps.signatures.append({"role": role, "fio": fio, "position": position})
    return f"Подпись сохранена: {role}"


# --------------------------------------------------------------------------- #
#  Capabilities: первый прогон (тип) и второй прогон (заполнение)             #
# --------------------------------------------------------------------------- #


class TypeDetector(AbstractCapability):
    @staticmethod
    def get_toolset() -> FunctionToolset:
        return FunctionToolset(tools=[set_doc_type])


class DocumentFiller(AbstractCapability):
    @staticmethod
    def get_toolset() -> FunctionToolset:
        return FunctionToolset(tools=[set_header, add_row, set_total, set_signature])


# Реестр «тип → набор tools» (Strategy). Новые типы документов добавляются сюда.
TOOLSETS: dict[DocType, AbstractCapability] = {
    DocType.TORG12: DocumentFiller(),
    DocType.INVOICE: DocumentFiller(),
    DocType.ACT: DocumentFiller(),
    DocType.CUSTOM: DocumentFiller(),
}

FILL_PROMPT = (
    "Распознай документ на картинке и вызывай tools, чтобы заполнить все видимые поля. "
    "Правила: поля, закрытые серыми прямоугольниками, не выдумывай — передавай null; "
    "даты нормализуй к YYYY-MM-DD; суммы передавай числом (через точку); "
    "итоговую сумму прописью записывай в поле total_in_words шапки."
)

def build_model():
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider
    return OpenAIResponsesModel(
        settings.model_name,
        provider=OpenAIProvider(
            base_url=settings.model_url,
            api_key=settings.model_key or "not-set",
        ),
    )


# --------------------------------------------------------------------------- #
#  Публичный API                                                               #
# --------------------------------------------------------------------------- #


async def recognize(image: bytes, media_type: str = "image/png") -> Document:
    """Полный цикл: шаг 1 — тип документа, шаг 2 — заполнение набором tools."""
    model = build_model()
    content = [BinaryContent(data=image, media_type=media_type)]

    # Шаг 1: лёгкий прогон — определение типа
    rec = Recorder()
    detector = Agent(model, name="Определение типа",
                     capabilities=[Caching(), TypeDetector()], deps_type=Recorder)
    await detector.run(
        ["Определи тип документа на картинке и вызови set_doc_type."] + content,
        deps=rec,
    )
    doc_type = rec.doc_type or DocType.CUSTOM

    # Шаг 2: повторный прогон с набором tools по типу (Strategy)
    filler = Agent(model, name="Заполнение документа",
                   capabilities=[Caching(), TOOLSETS[doc_type]], deps_type=Recorder)
    await filler.run([FILL_PROMPT] + content, deps=rec)

    return rec.build()