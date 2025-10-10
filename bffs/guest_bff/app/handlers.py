from datetime import datetime, date
import calendar
import asyncio
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from collections.abc import Mapping
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, Request
from httpx import AsyncClient, HTTPError
import os
import boto3
from jose import jwt
import httpx

from models.review import Review
from models.booking import Booking, BookingStatus
from models.user import UserResponse, UserUpdate
from models.property import Amenity, Property, PropertyDetail, Room
from models.payment import (
    CapturePaymentRequest,
    CapturePaymentResponse,
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    Money,
)
import logging

logger = logging.getLogger()


class JWTVerifier:
    def __init__(self, jwks_url: str, audience: str, env: str = "local") -> None:
        self.jwks_url = jwks_url
        self.audience = audience
        self.env = env
        self._jwks: dict | None = None

    async def _load_jwks(self) -> dict:
        if self._jwks is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.jwks_url, timeout=5)
                resp.raise_for_status()
                self._jwks = resp.json()
        return self._jwks # type: ignore

    async def get_current_user_id(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if not auth and self.env != "prod":
            xuid = request.headers.get("X-User-Id")
            if xuid:
                return xuid
        if not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = auth.split(" ", 1)[1]

        jwks = await self._load_jwks()
        try:
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get("kid")
            alg = unverified.get("alg")
            key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            if not key:
                # try refresh once for rotation
                self._jwks = None
                jwks = await self._load_jwks()
                key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            if not key:
                raise HTTPException(status_code=401, detail="JWKS key not found for token")

            claims = jwt.decode(
                token,
                key,
                audience=self.audience,
                algorithms=[alg] if alg else ["RS256"],
                options={"verify_at_hash": False},
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

        return str(claims.get("custom:user_uuid") or claims.get("sub"))


def get_jwt_verifier(request: Request) -> JWTVerifier:
    return request.app.state.jwt_verifier


async def get_current_user_uuid(
    request: Request,
    verifier: JWTVerifier = Depends(get_jwt_verifier),
) -> UUID:
    return UUID(await verifier.get_current_user_id(request))


def get_review_service_client(request: Request) -> AsyncClient:
    return request.app.state.review_service_client

def get_booking_service_client(request: Request) -> AsyncClient:
    return request.app.state.booking_service_client

def get_property_service_client(request: Request) -> AsyncClient:
    return request.app.state.property_service_client

def get_user_service_client(request: Request) -> AsyncClient:
    return request.app.state.user_service_client

def get_event_bus(request: Request):
    return request.app.state.event_bus

def get_place_index(request: Request):
    return request.app.state.place_index


def _forward_auth_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth
    elif request.app.state.app_metadata.guest_bff_env != "prod":
        xuid = request.headers.get("X-User-Id")
        if xuid:
            headers["X-User-Id"] = xuid
    return headers

def _extract_room_value(room_payload: Any, key: str) -> Any:
    if isinstance(room_payload, Mapping):
        return room_payload.get(key)
    return getattr(room_payload, key, None)

def _resolve_room_price(room_payload: Any, *keys: str) -> Decimal | None:
    for key in keys:
        value = _extract_room_value(room_payload, key)
        if value is not None:
            return Decimal(str(value))
    return None

def _normalize_date(value: date | datetime | None) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value

def _add_months(source: date, months: int) -> date:
    month_index = source.month - 1 + months
    year = source.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def _determine_nightly_price(room_payload: Any, check_in: date | None) -> Decimal:
    base_price = _resolve_room_price(room_payload, 'price_per_night', 'pricePerNight', 'price_perNight')
    if base_price is None:
        raise HTTPException(status_code=502, detail="Room pricing information unavailable")

    normalized_check_in = _normalize_date(check_in)
    if not normalized_check_in:
        return base_price

    min_price = _resolve_room_price(room_payload, 'min_price_per_night', 'minPricePerNight', 'min_pricePerNight')
    max_price = _resolve_room_price(room_payload, 'max_price_per_night', 'maxPricePerNight', 'max_pricePerNight')

    today = date.today()
    days_until_check_in = (normalized_check_in - today).days
    six_months_out = _add_months(today, 6)

    if normalized_check_in > six_months_out and min_price is not None:
        return min_price
    if days_until_check_in <= 10 and max_price is not None:
        return max_price
    return base_price

def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

PAYPAL_DEFAULT_BASE_URL = "https://api-m.sandbox.paypal.com"
PAYPAL_HTTP_TIMEOUT = 20.0

def _get_paypal_settings(request: Request) -> tuple[str, str, str]:
    client_id = getattr(request.app.state, "paypal_client_id", None) or os.environ.get("PAYPAL_CLIENT_ID")
    secret = getattr(request.app.state, "paypal_client_secret", None) or os.environ.get("PAYPAL_CLIENT_SECRET")
    base_url = (
        getattr(request.app.state, "paypal_base_url", None)
        or os.environ.get("PAYPAL_BASE_URL")
        or PAYPAL_DEFAULT_BASE_URL
    )
    if not client_id or not secret:
        logger.error("PayPal integration missing credentials. client_id_present=%s secret_present=%s", bool(client_id), bool(secret))
        raise HTTPException(status_code=500, detail="PayPal integration is not configured")
    return client_id, secret, base_url.rstrip('/')

async def _paypal_access_token(request: Request) -> tuple[str, str]:
    client_id, secret, base_url = _get_paypal_settings(request)
    logger.info(f"PAYPAL SETTINGS {client_id} {secret} {base_url}")
    async with AsyncClient(timeout=PAYPAL_HTTP_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, secret),
            )
            logger.info(f"PAYPAL oauth response {resp.status_code}")
            resp.raise_for_status()
        except HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"PayPal auth failed: {exc}") from exc
    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Missing access token from PayPal response")
    return token, base_url

def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

def _compute_booking_amount(room_payload: dict[str, Any], check_in: date, check_out: date) -> tuple[Decimal, Decimal, int, str]:
    nights = (check_out - check_in).days
    if nights <= 0:
        raise HTTPException(status_code=400, detail='Check-out date must be after check-in date')

    nightly_price = _determine_nightly_price(room_payload, check_in)
    total = (nightly_price * nights).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    nightly = nightly_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    currency = _extract_room_value(room_payload, 'currency_code') or 'USD'
    return total, nightly, nights, currency

def _date_to_iso(value: date) -> str:
    return datetime.combine(value, datetime.min.time()).isoformat()

async def search_places(text: str,  index_name: str = Depends(get_place_index)) -> list[dict]:

    if not index_name:
        raise HTTPException(status_code=500, detail="PLACE_INDEX_NAME not configured")
    client = boto3.client("location")
    try:
        resp = client.search_place_index_for_text(IndexName=index_name, Text=text, MaxResults=5)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Places lookup failed: {e}")
    results: list[dict] = []
    for r in resp.get("Results", []):
        place = r.get("Place", {})
        point = place.get("Geometry", {}).get("Point", [])
        results.append({
            "place_id": place.get("Id") or place.get("Label"),
            "label": place.get("Label"),
            "country": place.get("CountryCode") or place.get("Country"),
            "city": place.get("Municipality"),
            "state": place.get("Region"),
            "address": (f"{place.get('AddressNumber')} {place.get('Street')}"
                        if place.get('AddressNumber') and place.get('Street') else place.get("Street")),
            "longitude": point[0] if len(point) == 2 else None,
            "latitude": point[1] if len(point) == 2 else None,
        })
    return results

async def fetch_property(
    property_uuid: UUID,
    request: Request,
    check_in_date: date | None = None,
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> PropertyDetail:
    headers = _forward_auth_headers(request)
    resp = await property_service_client.get(
        f"property/{str(property_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json() or {}

    rooms_resp = await property_service_client.get(
        "rooms",
        params={"property_uuid": str(property_uuid)},
        timeout=10.0,
        headers=headers or None,
    )
    rooms_payload = rooms_resp.json() if rooms_resp.status_code == 200 else []

    normalized_check_in = _normalize_date(check_in_date)
    if normalized_check_in:
        adjusted_rooms: list[dict[str, Any]] = []
        for room_data in rooms_payload:
            nightly_decimal = _determine_nightly_price(room_data, normalized_check_in)
            room_data['price_per_night'] = float(_quantize_currency(nightly_decimal))
            adjusted_rooms.append(room_data)
        rooms_payload = adjusted_rooms

    data["rooms"] = rooms_payload

    return PropertyDetail(**data)

async def fetch_room(
    room_uuid: UUID,
    request: Request,
    check_in_date: date | None = None,
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> Room:
    headers = _forward_auth_headers(request)
    resp = await property_service_client.get(
        f"room/{str(room_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()

    normalized_check_in = _normalize_date(check_in_date)
    if normalized_check_in:
        nightly_decimal = _determine_nightly_price(data, normalized_check_in)
        data['price_per_night'] = float(_quantize_currency(nightly_decimal))

    return Room(**data)

async def add_review(
    review: Review,
    request: Request,
    review_service_client: AsyncClient = Depends(get_review_service_client),
    verifier: JWTVerifier = Depends(get_jwt_verifier),
    event_bus = Depends(get_event_bus),
    user_service_client: AsyncClient = Depends(get_user_service_client),
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> UUID:
    user_uuid = await verifier.get_current_user_id(request)
    headers = _forward_auth_headers(request)
    payload = review.model_dump(exclude_none=True)
    payload["user_uuid"] = user_uuid

    resp = await review_service_client.post(
        f"review/{str(review.property_uuid)}",
        json=payload,
        timeout=10.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    review_uuid = UUID(body if isinstance(body, str) else body.get("uuid"))
    reviewer_name = None
    host_email = None
    try:
        me = await user_service_client.get("me", headers=headers or None, timeout=10.0)
        if me.status_code == 200:
            me_body = me.json()
            me_obj = UserResponse(**me_body)
            reviewer_name = f"{me_obj.name} {me_obj.last_name}"
        prop_response = await property_service_client.get(
            f"/property/{str(review.property_uuid)}",
            timeout=10.0,
            headers=headers or None,
        )
        if prop_response.status_code == 200:
            prop = prop_response.json()
            prop_obj = Property(**prop)
            host_uuid = prop_obj.user_uuid
            if host_uuid:
                host_resp = await user_service_client.get(
                    f"user/{str(host_uuid)}",
                    headers=headers or None,
                    timeout=10.0,
                )
                if host_resp.status_code == 200:
                    host_body = host_resp.json() or {}
                    host_obj = UserResponse(**host_body)
                    host_email = host_obj.email
    except Exception:
        pass
    try:
        event_bus.put_event(
            detail_type="ReviewCreated",
            source="review-service",
            detail={
                "rating": review.rating,
                "reviewer_name": reviewer_name,
                "host_email": host_email,
            },
        )
    except Exception:
        pass
    return review_uuid

def _paypal_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
        "PayPal-Request-Id": str(uuid4()),  # idempotency
    }


async def create_payment_order(
    payload: CreatePaymentOrderRequest,
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> CreatePaymentOrderResponse:
    headers = _forward_auth_headers(request)
    room_response = await property_service_client.get(
        f"room/{str(payload.room_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )

    logger.info(f"Room response status code {room_response.status_code}")

    if room_response.status_code != 200:
        raise HTTPException(status_code=room_response.status_code, detail=room_response.text)
    room_payload = room_response.json()

    total, nightly, nights, currency = _compute_booking_amount(
        room_payload,
        payload.check_in,
        payload.check_out,
    )
    
    logger.info(f"{total} {nightly} {nights} {currency}")

    token, base_url = await _paypal_access_token(request)
    logger.info(f"Token {token} bas_url {base_url}")
    order_body = {
        "intent": "capture",
        "purchase_units": [
            {
                "reference_id": str(payload.room_uuid),
                "custom_id": str(current_user_uuid),
                "description": (f"Room booking - {room_payload.get('name', 'Room')}"[:127]),
                "amount": {
                    "currency_code": currency,
                    "value": _format_decimal(total),
                },
            }
        ],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
        },
    }

    async with AsyncClient(timeout=PAYPAL_HTTP_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{base_url}/v2/checkout/orders",
                json=order_body,
                headers=_paypal_headers(token),
            )
            logger.info(f"RESPONSE {response.status_code}")
            response.raise_for_status()
        except HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to create PayPal order: {exc}") from exc

    order_payload = response.json()
    order_id = order_payload.get("id")
    if not order_id:
        raise HTTPException(status_code=502, detail="Invalid response from PayPal order creation")

    return CreatePaymentOrderResponse(
        order_id=order_id,
        amount=Money(currency_code=currency, value=_format_decimal(total)),
        nights=nights,
        nightly_rate=_format_decimal(nightly),
        room_name=room_payload.get("name", ""),
        paypal_client_id=getattr(request.app.state, "paypal_client_id", None),
    )


async def capture_payment_order(
    payload: CapturePaymentRequest,
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    property_service_client: AsyncClient = Depends(get_property_service_client),
    user_service_client: AsyncClient = Depends(get_user_service_client),
    event_bus=Depends(get_event_bus),
) -> CapturePaymentResponse:
    headers = _forward_auth_headers(request)
    room_response = await property_service_client.get(
        f"room/{str(payload.room_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )
    if room_response.status_code != 200:
        raise HTTPException(status_code=room_response.status_code, detail=room_response.text)
    room_payload = room_response.json()

    total, _, _, currency = _compute_booking_amount(
        room_payload,
        payload.check_in,
        payload.check_out,
    )

    token, base_url = await _paypal_access_token(request)

    async with AsyncClient(timeout=PAYPAL_HTTP_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{base_url}/v2/checkout/orders/{payload.order_id}/capture",
                headers=_paypal_headers(token),
            )
            response.raise_for_status()
        except HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to capture PayPal order: {exc}") from exc

    capture_payload = response.json()
    status = capture_payload.get("status")
    purchase_units = capture_payload.get("purchase_units") or []
    payments = purchase_units[0].get("payments") if purchase_units else {}
    captures = payments.get("captures") or []
    capture_amount = None
    if captures:
        capture_amount = captures[0].get("amount")
        status = captures[0].get("status", status)

    if status not in {"COMPLETED", "APPROVED"}:
        raise HTTPException(status_code=502, detail=f"Unexpected PayPal capture status: {status}")

    paid_value = capture_amount.get("value") if capture_amount else None
    paid_currency = capture_amount.get("currency_code") if capture_amount else currency
    if paid_value is None:
        raise HTTPException(status_code=502, detail="PayPal capture did not return an amount")

    paid_total = Decimal(str(paid_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if paid_total != total:
        raise HTTPException(status_code=400, detail="Captured amount does not match expected total")

    booking_payload = {
        "uuid": str(uuid4()),
        "room_uuid": str(payload.room_uuid),
        "check_in": _date_to_iso(payload.check_in),
        "check_out": _date_to_iso(payload.check_out),
        "total_price": float(total),
        "status": BookingStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat() + 'Z',
        "updated_at": datetime.utcnow().isoformat() + 'Z',
    }

    booking_uuid = await add_booking(
        request,
        booking_payload,
        current_user_uuid,
        booking_service_client,
        event_bus,
        property_service_client,
        user_service_client,
    )

    return CapturePaymentResponse(
        booking_uuid=booking_uuid,
        payment_status="COMPLETED",
        amount=Money(currency_code=paid_currency or currency, value=_format_decimal(total)),
    )
async def add_booking(
    request: Request,
    booking: dict,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    event_bus = Depends(get_event_bus),
    property_service_client: AsyncClient = Depends(get_property_service_client),
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UUID:
    headers = _forward_auth_headers(request)
    payload = dict(booking)
    payload["user_uuid"] = str(current_user_uuid)
    resp = await booking_service_client.post(
        "booking",
        json=payload,
        timeout=15.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    booking_uuid = UUID(body if isinstance(body, str) else body.get("uuid"))
    # Emit BookingConfirmed event for notifications, enriched with guest/host/property
    try:
        # guest email
        guest_email = None
        me = await user_service_client.get("me", headers=headers or None, timeout=10.0)
        if me.status_code == 200:
            me_body = me.json() or {}
            guest_email = me_body.get("email")

        # property name and host email via room -> property -> host user
        property_name = None
        host_email = None
        room_uuid = booking.get("room_uuid") if isinstance(booking, dict) else None
        check_in = booking.get("check_in") if isinstance(booking, dict) else None
        if room_uuid:
            room_response = await property_service_client.get(
                f"room/{str(room_uuid)}",
                timeout=10.0,
                headers=headers or None,
            )
            if room_response.status_code == 200:
                room_body = room_response.json()
                room_obj = Room(**room_body)
                prop_uuid =room_obj.property_uuid
                if prop_uuid:
                    prop_resp = await property_service_client.get(
                        f"property/{str(prop_uuid)}",
                        timeout=10.0,
                        headers=headers or None,
                    )
                    if prop_resp.status_code == 200:
                        prop_body = prop_resp.json()
                        prop_obj = Property(**prop_body)
                        property_name = prop_obj.name
                        host_uuid = prop_obj.user_uuid
                        if host_uuid:
                            user_resp = await user_service_client.get(
                                f"user/{str(host_uuid)}",
                                headers=headers or None,
                                timeout=10.0,
                            )
                            if user_resp.status_code == 200:
                                user_body = user_resp.json()
                                user_obj = UserResponse(**user_body)
                                host_email = user_obj.email

        event_bus.put_event(
            detail_type="BookingConfirmed",
            source="booking-service",
            detail={
                "guest_email": guest_email,
                "property_name": property_name,
                "check_in": check_in,
                "host_email": host_email,
            },
        )
    except Exception:
        pass
    return booking_uuid


async def get_user_bookings(
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> list[Booking]:
    headers = _forward_auth_headers(request)
    resp = await booking_service_client.get(
        "bookings",
        params={"user_uuid": str(current_user_uuid)},
        timeout=15.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    items = resp.json() or []
    return [Booking(**it) for it in items]


async def cancel_user_booking(
    booking_uuid: UUID,
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> UUID:
    headers = _forward_auth_headers(request)
    resp = await booking_service_client.patch(
        f"booking/{str(booking_uuid)}/cancel",
        json={"user_uuid": str(current_user_uuid)},
        timeout=15.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    return UUID(body if isinstance(body, str) else body.get("uuid"))


async def get_current_user(
    request: Request,
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UserResponse:
    auth = request.headers.get("Authorization", "")
    resp = await user_service_client.get("me", headers={"Authorization": auth}, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return UserResponse(**resp.json())


async def update_current_user(
    update: UserUpdate,
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UserResponse | None:
    auth = request.headers.get("Authorization", "")
    payload = update.model_dump(exclude_none=True)
    resp = await user_service_client.patch(
        f"user/{str(current_user_uuid)}",
        json=payload,
        headers={"Authorization": auth},
        timeout=10.0,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    return None if body is None else UserResponse(**body)


async def get_property_reviews(
    property_uuid: UUID,
    request: Request,
    review_service_client: AsyncClient = Depends(get_review_service_client),
) -> list[Review]:
    headers = _forward_auth_headers(request)
    resp = await review_service_client.get(
        f"reviews/{str(property_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    reviews_response = resp.json() or []
    return [Review(**review) for review in reviews_response]


async def get_user_reviews(
    user_uuid: UUID,
    request: Request,
    review_service_client: AsyncClient = Depends(get_review_service_client),
) -> list[Review]:
    headers = _forward_auth_headers(request)
    resp = await review_service_client.get(
        f"reviews/{str(user_uuid)}",
        timeout=10.0,
        headers=headers or None,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    reviews_response = resp.json() or []
    return [Review(**review) for review in reviews_response]


async def get_filtered_rooms(
    request: Request,
    check_in_date: date | None = None,
    check_out_date: date | None = None,
    amenities: list[Amenity] | None = None,
    capacity: int | None = None,
    max_price: float | None = None,
    country: str | None = None,
    state: str | None = None,
    city: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    rating_above: float | None = None,
    review_service_client: AsyncClient = Depends(get_review_service_client),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    property_service_client: AsyncClient = Depends(get_property_service_client),
):
    headers = _forward_auth_headers(request)
    properties = []
    if latitude is not None and longitude is not None and (radius_km is not None):
        prop_resp = await property_service_client.get(
            "properties/near",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                **({"country": country} if country else {}),
                **({"state": state} if state else {}),
                **({"city": city} if city else {}),
            },
            timeout=10.0,
            headers=headers or None,
        )
        if prop_resp.status_code != 200:
            raise HTTPException(status_code=prop_resp.status_code, detail=prop_resp.text)
        properties = [Property(**p) for p in (prop_resp.json() or [])]
    elif country and city:
        params = {"country": country, "city": city}
        if state:
            params["state"] = state
        property_response = await property_service_client.get(
            "properties/city",
            params=params,
            timeout=10.0,
            headers=headers or None,
        )
        if property_response.status_code != 200:
            raise HTTPException(status_code=property_response.status_code, detail=property_response.text)
        property_response = property_response.json()
        properties = [Property(**property) for property in property_response]

    room_results: list[PropertyDetail]= []
    room_filter_params = {}
    if capacity is not None:
        room_filter_params["capacity"] = capacity
    if max_price is not None:
        room_filter_params["max_price_per_night"] = max_price
    if amenities:
        room_filter_params["amenities"] = [a.name for a in amenities]

    if not properties:
        return []
    for property in properties:
        params = {"property_uuid": str(property.uuid)}
        params.update(room_filter_params)
        rooms_result = await property_service_client.get(
            "rooms",
            params=params,
            timeout=10.0,
            headers=headers or None,
        )
        if rooms_result.status_code != 200:
            raise HTTPException(status_code=rooms_result.status_code, detail=rooms_result.text)
        rooms_result = rooms_result.json()
        prop_detail = PropertyDetail(**property.model_dump())
        prop_detail.rooms = [Room(**room) for room in rooms_result]
        room_results.append(prop_detail)


    available_room_entries: list[PropertyDetail] = []
    date_filtered = bool(check_in_date and check_out_date)
    check_in_iso = check_in_date.isoformat() if check_in_date else None
    check_out_iso = check_out_date.isoformat() if check_out_date else None

    for prop in room_results:
        property_detail = PropertyDetail(**prop.model_dump())
        rooms_to_check = list(prop.rooms or [])
        if not rooms_to_check:
            continue
        if date_filtered:
            property_detail.rooms = []  # type: ignore[attr-defined]
            room_ids = [str(room.uuid) for room in rooms_to_check if room.uuid]
            if room_ids:
                payload = {
                    "room_uuids": room_ids,
                    "check_in": check_in_iso,
                    "check_out": check_out_iso,
                }
                availability_response = await booking_service_client.post(
                    "availability/batch",
                    json=payload,
                    timeout=10.0,
                    headers=headers or None,
                )
                if availability_response.status_code != 200:
                    raise HTTPException(status_code=availability_response.status_code, detail=availability_response.text)
                availability_map = availability_response.json() or {}
                for room in rooms_to_check:
                    if availability_map.get(str(room.uuid)):
                        property_detail.rooms.append(room)  # type: ignore[attr-defined]
            else:
                property_detail.rooms = rooms_to_check  # type: ignore[attr-defined]
        else:
            property_detail.rooms = rooms_to_check  # type: ignore[attr-defined]
        if property_detail.rooms:
            available_room_entries.append(property_detail)
                

    
    for prop_detail in available_room_entries:
        rev = await review_service_client.get(
            f"reviews/{str(prop_detail.uuid)}",
            timeout=10.0,
            headers=headers or None,
        )
        if rev.status_code != 200:
            raise HTTPException(status_code=rev.status_code, detail=rev.text)
        rev = rev.json()
        reviews = [Review(**review) for review in rev]
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)
        else:
            avg = None
        
        prop_detail.average_rating = avg

    normalized_check_in = _normalize_date(check_in_date)
    if normalized_check_in:
        for prop_detail in available_room_entries:
            rooms = list(prop_detail.rooms or [])
            if not rooms:
                continue
            adjusted_rooms: list[Room] = []
            for room in rooms:
                nightly_decimal = _determine_nightly_price(room, normalized_check_in)
                room.price_per_night = float(_quantize_currency(nightly_decimal))
                adjusted_rooms.append(room)
            prop_detail.rooms = adjusted_rooms  # type: ignore[attr-defined]

    if rating_above:
        available_room_entries = list(filter(lambda x: x.average_rating and x.average_rating>=rating_above, available_room_entries))

    return available_room_entries
