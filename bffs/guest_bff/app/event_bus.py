from __future__ import annotations

import json
from typing import Any

import boto3


class EventBusClient:
    def __init__(self, bus_name: str | None):
        if not bus_name:
            raise ValueError("EVENT_BUS_NAME must be provided")
        self.bus_name = bus_name
        self.client = boto3.client("events")

    def put_event(self, detail_type: str, source: str, detail: dict[str, Any]) -> None:
        self.client.put_events(
            Entries=[
                {
                    "EventBusName": self.bus_name,
                    "Source": source,
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail, default=str),
                }
            ]
        )

