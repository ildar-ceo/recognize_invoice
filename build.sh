#!/usr/bin/env bash
# Сборка и управление Docker-образом проекта.
# Использование: ./build.sh <команда>
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-invoice-recognition}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

usage() {
    cat <<EOF
Сборка контейнера системы распознавания документов.

Использование: $0 <команда>

Команды:
  docker    Собрать Docker-образ (тег: ${IMAGE_NAME}:${IMAGE_TAG})
  help      Показать эту справку

Переменные окружения:
  IMAGE_NAME  Имя образа  (по умолчанию: ${IMAGE_NAME})
  IMAGE_TAG   Тег образа   (по умолчанию: ${IMAGE_TAG})
EOF
}

cmd="${1:-}"

case "$cmd" in
    docker)
        echo "Сборка образа ${IMAGE_NAME}:${IMAGE_TAG}..."
        docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
        echo "Готово: ${IMAGE_NAME}:${IMAGE_TAG}"
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        # Команда не задана или неизвестна — выводим справку
        usage
        ;;
esac