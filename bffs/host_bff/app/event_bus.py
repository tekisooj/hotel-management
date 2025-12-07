import json
from typing import Any

import boto3


class EventBusClient:
    def __init__(self, event_bus_name: str | None):
        if not event_bus_name:
            raise ValueError("EVENT_BUS_NAME must be provided")
        self.event_bus_name = event_bus_name
        self.client = boto3.client("events")

    def put_event(self, detail_type: str, source: str, detail: dict[str, Any]) -> None:
        self.client.put_events(
            Entries=[
                {
                    "EventBusName": self.event_bus_name,
                    "Source": source,
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail, default=str),
                }
            ]
        )
