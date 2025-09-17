from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID

from schemas import Image


def strip_image_urls(images: list[Image] | None) -> None:
    if not images:
        return
    for image in images:
        if hasattr(image, "url"):
            image.url = None


def create_image_url(images: Iterable[Image] | None, storage) -> None:
    if not storage or not images:
        return
    for image in images:
        key = getattr(image, "key", None)
        if key:
            image.url = storage.create_read_url(key)


def add_image_url(model: Any, storage) -> Any:
    images = getattr(model, "images", None)
    create_image_url(images, storage)
    return model


def add_image_urls(models: Iterable[Any] | None, storage) -> Iterable[Any]:
    if not models or not storage:
        return models or []
    for model in models:
        add_image_url(model, storage)
    return models


def to_dynamodb_item(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dynamodb_item = {}

    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, str):
            dynamodb_item[key] = {"S": value}
        elif isinstance(value, bool):
            dynamodb_item[key] = {"BOOL": value}
        elif isinstance(value, (int, Decimal)):
            dynamodb_item[key] = {"N": str(value)}
        elif isinstance(value, float):
            dynamodb_item[key] = {"N": str(Decimal(str(value)))}
        elif isinstance(value, UUID):
            dynamodb_item[key] = {"S": str(value)}
        elif isinstance(value, datetime):
            dynamodb_item[key] = {"S": value.isoformat()}
        elif isinstance(value, list):
            dynamodb_item[key] = {"L": [to_dynamodb_item({"tmp": v})["tmp"] for v in value]}
        elif isinstance(value, dict):
            dynamodb_item[key] = {"M": to_dynamodb_item(value)}
        else:
            raise TypeError(f"Unsupported type for key '{key}': {type(value)}")

    return dynamodb_item


def from_dynamodb_item(item: dict[str, dict[str, Any]]) -> dict[str, Any]:
    python_dict: dict[str, Any] = {}

    for key, value in item.items():
        if "S" in value:
            raw = value["S"]

            try:
                python_dict[key] = UUID(raw)
                continue
            except ValueError:
                pass

            try:
                python_dict[key] = datetime.fromisoformat(raw)
                continue
            except ValueError:
                pass

            python_dict[key] = raw

        elif "N" in value:
            number = value["N"]

            if "." in number:
                python_dict[key] = float(number)
            else:
                python_dict[key] = int(number)

        elif "BOOL" in value:
            python_dict[key] = value["BOOL"]

        elif "L" in value:
            python_dict[key] = [
                from_dynamodb_item({"tmp": v})["tmp"] for v in value["L"]
            ]

        elif "M" in value:
            python_dict[key] = from_dynamodb_item(value["M"])

        else:
            raise TypeError(f"Unsupported DynamoDB type for key '{key}': {value}")

    return python_dict
