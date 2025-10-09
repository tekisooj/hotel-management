from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field, conint


class Money(BaseModel):
    currency_code: str = Field(default="USD", description="ISO currency code")
    value: str = Field(description="Formatted amount with 2 decimals")


class CreatePaymentOrderRequest(BaseModel):
    room_uuid: UUID = Field(alias="room_uuid")
    check_in: date
    check_out: date
    guests: conint(gt=0) = 1

    class Config:
        populate_by_name = True


class CreatePaymentOrderResponse(BaseModel):
    order_id: str = Field(alias="order_id")
    amount: Money
    nights: int
    nightly_rate: str
    room_name: str
    paypal_client_id: str | None = None

    class Config:
        populate_by_name = True


class CapturePaymentRequest(BaseModel):
    order_id: str = Field(alias="order_id")
    room_uuid: UUID = Field(alias="room_uuid")
    check_in: date
    check_out: date
    guests: conint(gt=0) = 1

    class Config:
        populate_by_name = True


class CapturePaymentResponse(BaseModel):
    booking_uuid: UUID
    payment_status: str
    amount: Money

