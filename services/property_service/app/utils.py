from typing import Any
from uuid import UUID
from datetime import datetime


def to_dynamodb_item(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dynamodb_item = {}

    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, str):
            dynamodb_item[key] = {"S": value}
        elif isinstance(value, bool):
            dynamodb_item[key] = {"BOOL": value}
        elif isinstance(value, int) or isinstance(value, float):
            dynamodb_item[key] = {"N": str(value)}
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
    python_dict = {}

    for key, value in item.items():
        if "S" in value:
            python_dict[key] = value["S"]
        elif "N" in value:
            number = value["N"]
            python_dict[key] = float(number) if '.' in number else int(number)
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

