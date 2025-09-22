from datetime import datetime
import asyncio
from uuid import UUID
from fastapi import Depends, HTTPException, Request
from httpx import AsyncClient, HTTPError
import os
import boto3
from jose import jwt
import httpx

from models.review import Review
from models.booking import Booking
from models.user import UserResponse, UserUpdate
from models.property import Amenity, Property, PropertyDetail, Room


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
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> Property:
    resp = await property_service_client.get(f"property/{str(property_uuid)}", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return Property(**data)

async def fetch_room(
    room_uuid: UUID,
    property_service_client: AsyncClient = Depends(get_property_service_client),
) -> Room:
    resp = await property_service_client.get(f"room/{str(room_uuid)}", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
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
    payload = review.model_dump(exclude_none=True)
    payload["user_uuid"] = user_uuid

    resp = await review_service_client.post(
        f"/review/{str(review.property_uuid)}",
        json=payload,
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    review_uuid = UUID(body if isinstance(body, str) else body.get("uuid"))
    reviewer_name = None
    host_email = None
    try:
        auth = request.headers.get("Authorization", "")
        me = await user_service_client.get("me", headers={"Authorization": auth}, timeout=10.0)
        if me.status_code == 200:
            me_body = me.json()
            me_obj = UserResponse(**me_body)
            reviewer_name = f"{me_obj.name} {me_obj.last_name}"
        prop_response = await property_service_client.get(f"/property/{str(review.property_uuid)}", timeout=10.0)
        if prop_response.status_code == 200:
            prop = prop_response.json()
            prop_obj = Property(**prop)
            host_uuid = prop_obj.user_uuid
            if host_uuid:
                host_resp = await user_service_client.get(f"user/{str(host_uuid)}", headers={"Authorization": auth}, timeout=10.0)
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


async def add_booking(
    request: Request,
    booking: dict,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    event_bus = Depends(get_event_bus),
    property_service_client: AsyncClient = Depends(get_property_service_client),
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UUID:
    payload = dict(booking)
    payload["user_uuid"] = str(current_user_uuid)
    resp = await booking_service_client.post("booking", json=payload, timeout=15.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    body = resp.json()
    booking_uuid = UUID(body if isinstance(body, str) else body.get("uuid"))
    # Emit BookingConfirmed event for notifications, enriched with guest/host/property
    try:
        auth = request.headers.get("Authorization", "")
        # guest email
        guest_email = None
        me = await user_service_client.get("me", headers={"Authorization": auth}, timeout=10.0)
        if me.status_code == 200:
            me_body = me.json() or {}
            guest_email = me_body.get("email")

        # property name and host email via room -> property -> host user
        property_name = None
        host_email = None
        room_uuid = booking.get("room_uuid") if isinstance(booking, dict) else None
        check_in = booking.get("check_in") if isinstance(booking, dict) else None
        if room_uuid:
            room_response = await property_service_client.get(f"room/{str(room_uuid)}", timeout=10.0)
            if room_response.status_code == 200:
                room_body = room_response.json()
                room_obj = Room(**room_body)
                prop_uuid =room_obj.property_uuid
                if prop_uuid:
                    prop_resp = await property_service_client.get(f"property/{str(prop_uuid)}", timeout=10.0)
                    if prop_resp.status_code == 200:
                        prop_body = prop_resp.json()
                        prop_obj = Property(**prop_body)
                        property_name = prop_obj.name
                        host_uuid = prop_obj.user_uuid
                        if host_uuid:
                            user_resp = await user_service_client.get(f"user/{str(host_uuid)}", headers={"Authorization": auth}, timeout=10.0)
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
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> list[Booking]:
    resp = await booking_service_client.get(
        "bookings",
        params={"user_uuid": str(current_user_uuid)},
        timeout=15.0,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    items = resp.json() or []
    return [Booking(**it) for it in items]


async def cancel_user_booking(
    booking_uuid: UUID,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> UUID:
    resp = await booking_service_client.patch(
        f"booking/{str(booking_uuid)}/cancel",
        json={"user_uuid": str(current_user_uuid)},
        timeout=15.0,
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
    review_service_client: AsyncClient = Depends(get_review_service_client),
) -> list[Review]:
    resp = await review_service_client.get(f"reviews/{str(property_uuid)}", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    reviews_response = resp.json() or []
    return [Review(**review) for review in reviews_response]


async def get_user_reviews(
    user_uuid: UUID,
    review_service_client: AsyncClient = Depends(get_review_service_client),
) -> list[Review]:
    resp = await review_service_client.get(f"reviews/{str(user_uuid)}", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    reviews_response = resp.json() or []
    return [Review(**review) for review in reviews_response]


async def get_filtered_rooms(
    check_in_date: datetime | None = None,
    check_out_date: datetime | None = None,
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
        )
        if prop_resp.status_code != 200:
            raise HTTPException(status_code=prop_resp.status_code, detail=prop_resp.text)
        properties = [Property(**p) for p in (prop_resp.json() or [])]
    elif country and city:
        params = {"country": country, "city": city}
        if state:
            params["state"] = state
        property_response = await property_service_client.get("properties/city", params=params, timeout=10.0)
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
        raise ValueError("Location must be provided.")

    for property in properties:
        params = {"property_uuid": str(property.uuid)}
        params.update(room_filter_params)
        rooms_result = await property_service_client.get("rooms", params=params, timeout=10.0)
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

            async def fetch_availability(room: Room):
                response = await booking_service_client.get(
                    f"availability/{str(room.uuid)}",
                    params={"check_in": check_in_iso, "check_out": check_out_iso},
                    timeout=10.0,
                )
                return room, response

            results = await asyncio.gather(*(fetch_availability(room) for room in rooms_to_check), return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    raise HTTPException(status_code=502, detail=str(result))
                room, avail_response = result
                if avail_response.status_code != 200:
                    raise HTTPException(status_code=avail_response.status_code, detail=avail_response.text)
                if bool(avail_response.json()):
                    property_detail.rooms.append(room)  # type: ignore[attr-defined]
        if property_detail.rooms:
            available_room_entries.append(property_detail)
                

    
    for prop_detail in available_room_entries:
        rev = await review_service_client.get(f"reviews/{str(prop_detail.uuid)}", timeout=10.0)
        if rev.status_code != 200:
            raise HTTPException(status_code=rev.status_code, detail=rev.text)
        rev = rev.json()
        reviews = [Review(**review) for review in rev]
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)
        else:
            avg = None
        
        prop_detail.average_rating = avg

    if rating_above:
        available_room_entries = list(filter(lambda x: x.average_rating and x.average_rating>=rating_above, available_room_entries))

    return available_room_entries


