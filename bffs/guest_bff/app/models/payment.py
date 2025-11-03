from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field, conint


class Money(BaseModel):
    currency_code: str = Field(default="USD", description="ISO currency code")
    value: str = Field(description="Formatted amount with 2 decimals")


class CreatePaymentOrderRequest(BaseModel):
    room_uuid: UUID = Field(description="Room uuid")
    check_in: date = Field(description="Check in date")
    check_out: date = Field(description="Check out date")
    guests: int = Field(description="Number of guests", gt=1)

    class Config:
        populate_by_name = True


class CreatePaymentOrderResponse(BaseModel):
    order_id: str = Field(description="Order id")
    amount: Money = Field(description="Price")
    nights: int = Field(description="Number of nights")
    nightly_rate: str = Field(description="Price for one night")
    room_name: str = Field(description="Room name")
    paypal_client_id: str | None = None

    class Config:
        populate_by_name = True


class CapturePaymentRequest(BaseModel):
    order_id: str = Field(description="Order id")
    room_uuid: UUID = Field(description="Room uuid")
    check_in: date = Field(description="Check in date")
    check_out: date = Field(description="Check out date")
    guests: int = Field(description="Number of guests", gt=1)

    class Config:
        populate_by_name = True


class CapturePaymentResponse(BaseModel):
    booking_uuid: UUID = Field(description="Booking uuid")
    payment_status: str = Field(description="Payment status")
    amount: Money = Field(description="Price")

