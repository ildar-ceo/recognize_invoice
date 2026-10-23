"""Настройки приложения: чтение из env / .env и сохранение со страницы настроек."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(".env")
_ENV_KEYS = ("MODEL_NAME", "MODEL_KEY", "MODEL_URL")


class Settings(BaseSettings):
    model_name: str = ""
    model_key: str = ""
    model_url: str = ""

    # режим отладки: при DEBUG=1 включается автоперезагрузка при изменении файлов
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        protected_namespaces=(),
        extra="ignore",
    )


settings = Settings()


def save_settings(model_name: str, model_key: str, model_url: str) -> None:
    """Обновить настройки в памяти и записать их в .env (сохраняя комментарии и другие ключи)."""
    settings.model_name = model_name
    settings.model_key = model_key
    settings.model_url = model_url

    values = {"MODEL_NAME": model_name, "MODEL_KEY": model_key, "MODEL_URL": model_url}
    old_comments: dict[str, str] = {}
    other_lines: list[str] = []  # строки вне _ENV_KEYS (например DEBUG), чтобы не потерять их
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            matched = False
            for key in _ENV_KEYS:
                if line.startswith(f"{key}="):
                    matched = True
                    if "#" in line:
                        old_comments[key] = line[line.index("#"):]
                    break
            if not matched and line.strip():
                other_lines.append(line)

    lines = [f"{k}={values[k]} {old_comments.get(k, '')}".rstrip() for k in _ENV_KEYS]
    lines.extend(other_lines)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")