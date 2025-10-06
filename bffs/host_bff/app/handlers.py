from datetime import datetime
import asyncio
from typing import Any
from uuid import UUID
from fastapi import Depends, HTTPException, Request
from httpx import AsyncClient, HTTPError
from jose import jwt
import httpx

from models.review import Review
from models.booking import Booking, BookingStatus
from models.user import UserResponse, UserUpdate
from models.property import Property, PropertyDetail, Room
from models.property import Availability
from models.asset import AssetUploadRequest, AssetUploadResponse
import os
import boto3


class JWTVerifier:
    def __init__(self, jwks_url: str | None = None, audience: str | None = None, env: str = "local") -> None:
        self.jwks_url = jwks_url
        self.audience = audience
        self.env = env
        self._jwks: dict | None = None

        if not self.jwks_url or not self.audience:
            raise Exception("Cognito data not properly set")

    async def _load_jwks(self) -> dict:
        if not self.jwks_url:
            raise Exception("Cognito data not properly set")
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

def get_place_index(request: Request) -> str | None:
    # Prefer value set on app state; fall back to env var
    place_index = getattr(request.app.state, "place_index", None)
    return place_index or os.environ.get("PLACE_INDEX_NAME")


def _forward_auth_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth
    else:
        env = getattr(getattr(request.app.state, "app_metadata", None), "host_bff_env", None)
        if env != "prod":
            xuid = request.headers.get("X-User-Id")
            if xuid:
                headers["X-User-Id"] = xuid
    return headers


def _extract_image_key(image: Any) -> str | None:
    if isinstance(image, dict):
        return image.get("key")
    return getattr(image, "key", None)


def _normalize_images_field(payload: dict[str, Any]) -> None:
    if "images" not in payload:
        return
    images = payload.get("images")
    if not images:
        payload["images"] = []
        return
    normalized: list[dict[str, str]] = []
    for image in images:
        key = _extract_image_key(image)
        if key:
            normalized.append({"key": key})
    payload["images"] = normalized


async def search_places(
    text: str,
    index: str | None = None,
    index_name: str | None = Depends(get_place_index),
) -> list[dict]:
    use_index = (index or index_name or "").strip()
    if not use_index:
        raise HTTPException(status_code=500, detail="PLACE_INDEX_NAME not configured; pass ?index=... or set env")
    client = boto3.client("location")
    try:
        resp = client.search_place_index_for_text(IndexName=use_index, Text=text, MaxResults=5)
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
            "address": place.get("AddressNumber") and place.get("Street") and f"{place.get('AddressNumber')} {place.get('Street')}" or place.get("Street"),
            "longitude": point[0] if len(point) == 2 else None,
            "latitude": point[1] if len(point) == 2 else None,
        })
    return results


async def get_user_properties(
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> list[PropertyDetail]:
    headers = _forward_auth_headers(request)

    response = await property_service_client.get(
        f"property/{str(current_user_uuid)}",
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    response_body = response.json()
    property_details = [PropertyDetail(**prop) for prop in response_body]

    for property_detail in property_details:
        rooms_response = await property_service_client.get(
            f"rooms/{str(property_detail.uuid)}",
            headers=headers or None,
        )
        if rooms_response.status_code != 200:
            raise HTTPException(status_code=rooms_response.status_code, detail=rooms_response.text)

        rooms_response_body = rooms_response.json()
        property_detail.rooms = [Room(**room) for room in rooms_response_body]

    return property_details

async def add_property(
    property: PropertyDetail,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    headers = _forward_auth_headers(request)
    prop = Property(**property.model_dump())
    prop_payload = prop.model_dump(mode="json", exclude_none=True)
    _normalize_images_field(prop_payload)
    response = await property_service_client.post(
        "property",
        json=prop_payload,
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    prop_uuid = response.json()

    rooms = property.rooms or []
    for room in rooms:
        room_payload = room.model_dump(mode="json", exclude_none=True)
        _normalize_images_field(room_payload)
        room_payload["property_uuid"] = prop_uuid
        response = await property_service_client.post(
            "room",
            json=room_payload,
            headers=headers or None,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    return prop_uuid

async def add_room(
    room: Room,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    headers = _forward_auth_headers(request)
    room_payload = room.model_dump(mode="json", exclude_none=True)
    _normalize_images_field(room_payload)
    response = await property_service_client.post(
        "room",
        json=room_payload,
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    room_uuid = response.json()
    return room_uuid

async def create_asset_upload_url(
    payload: AssetUploadRequest,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> AssetUploadResponse:
    headers = _forward_auth_headers(request)
    try:
        response = await property_service_client.post(
            "assets/upload-url",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=headers or None,
        )
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return AssetUploadResponse(**response.json())

async def delete_room(
    room_uuid: UUID,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    headers = _forward_auth_headers(request)
    response = await property_service_client.delete(
        f"room/{str(room_uuid)}",
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return room_uuid


async def delete_property(
    property_uuid: UUID,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    headers = _forward_auth_headers(request)
    response = await property_service_client.delete(
        f"property/{str(property_uuid)}",
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return property_uuid


async def change_booking_status(
    booking_uuid: UUID,
    booking_status: BookingStatus,
    request: Request,
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> Booking:
    headers = _forward_auth_headers(request)
    response = await booking_service_client.patch(
        "booking",
        json={"booking_uuid": str(booking_uuid), "status": booking_status.value},
        headers=headers or None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    response = response.json()
    return Booking(**response)

async def get_bookings(
    property_uuid: UUID,
    check_in: datetime,
    check_out: datetime,
    request: Request,
    property_service_client: AsyncClient = Depends(get_property_service_client),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> list[Availability]:
    headers = _forward_auth_headers(request)
    property_response = await property_service_client.get(
        f"property/{str(property_uuid)}",
        headers=headers or None,
    )
    if property_response.status_code != 200:
        raise HTTPException(status_code=property_response.status_code, detail=property_response.text)

    property_response = property_response.json()
    property_obj = Property(**property_response)

    availabilities: list[Availability] = []
    unique_user_ids: set[str] = set()

    rooms_response = await property_service_client.get(
        f"rooms/{str(property_obj.uuid)}",
        headers=headers or None,
    )
    if rooms_response.status_code != 200:
        raise HTTPException(status_code=rooms_response.status_code, detail=rooms_response.text)
    rooms_response = rooms_response.json()
    rooms = [Room(**room) for room in rooms_response]
    params = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
    }
    for room in rooms:
        params["room_uuid"] = str(room.uuid)
        bookings_response = await booking_service_client.get(
            "bookings",
            params=params,
            headers=headers or None,
        )
        if bookings_response.status_code != 200:
            raise HTTPException(status_code=bookings_response.status_code, detail=bookings_response.text)
        bookings_payload = bookings_response.json()
        availability = Availability(**room.model_dump())
        availability.property = property_obj
        room_bookings = [Booking(**booking) for booking in bookings_payload]
        availability.bookings = room_bookings
        for booking in room_bookings:
            unique_user_ids.add(str(booking.user_uuid))
        availabilities.append(availability)

    user_details: dict[str, dict[str, Any]] = {}

    if unique_user_ids:
        async def fetch_user(user_uuid: str) -> None:
            if user_uuid in user_details:
                return
            try:
                response = await user_service_client.get(
                    f"user/{user_uuid}",
                    headers=headers or None,
                )
            except HTTPError:
                return
            if response.status_code == 200:
                user_details[user_uuid] = response.json()

        await asyncio.gather(*(fetch_user(user_uuid) for user_uuid in unique_user_ids), return_exceptions=True)

    for availability in availabilities:
        if not availability.bookings:
            continue
        for booking in availability.bookings:
            user_info = user_details.get(str(booking.user_uuid))
            if not user_info:
                continue
            full_name = " ".join(
                part.strip()
                for part in [user_info.get("name", ""), user_info.get("last_name", "")]
                if part and part.strip()
            )
    return availabilities


async def get_current_user(
    request: Request,
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UserResponse:
    headers = _forward_auth_headers(request)
    resp = await user_service_client.get("me", headers=headers or None, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return UserResponse(**resp.json())


async def update_current_user(
    update: UserUpdate,
    request: Request,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UserResponse | None:
    headers = _forward_auth_headers(request)
    payload = update.model_dump(exclude_none=True)
    resp = await user_service_client.patch(
        f"user/{str(current_user_uuid)}",
        json=payload,
        headers=headers or None,
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

