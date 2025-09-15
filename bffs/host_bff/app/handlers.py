from datetime import datetime
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
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> list[PropertyDetail]:
    
    response = await property_service_client.get(f"/properties/{str(current_user_uuid)}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    response_body = response.json()
    property_details = [PropertyDetail(**prop) for prop in response_body]

    for property_detail in property_details:
        rooms_response = await property_service_client.get(f"/rooms/{str(property_detail.uuid)}")
        if rooms_response.status_code != 200:
            raise HTTPException(status_code=rooms_response.status_code, detail=rooms_response.text)

        rooms_response_body = rooms_response.json()
        property_detail.rooms = [Room(**room) for room in rooms_response_body]

    return property_details

# async def add_property(
#     property: PropertyDetail,
#     property_service_client: AsyncClient = Depends(get_property_service_client)
# ) -> UUID:
#     prop = Property(**property.model_dump(mode="json"))
#     response = await property_service_client.post(f"/property", json = prop.model_dump(mode="json"))
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
#     prop_uuid = response.json()

#     if not property.rooms:
#         return prop_uuid
    
#     for room in property.rooms:
        
#         response = await property_service_client.post(f"/room", json = room.model_dump(mode="json"))
#         if response.status_code != 200:
#             raise HTTPException(status_code=response.status_code, detail=response.text)

#     return prop_uuid

async def put_property(
    property: PropertyDetail,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    prop = Property(**property.model_dump(mode="json"))
    response = await property_service_client.post(f"/property", json = prop.model_dump(mode="json"))
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    prop_uuid = response.json()

    if not property.rooms:
        return prop_uuid
    
    for room in property.rooms:
        room_dict = room.model_dump(mode="json")
        room_dict["property_uuid"] = prop_uuid
        response = await property_service_client.post(f"/room", json = room_dict)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    return prop_uuid

# async def add_room(
#     room: Room,
#     property_service_client: AsyncClient = Depends(get_property_service_client)
# ) -> UUID:
#     response = await property_service_client.post(f"/room", json = room.model_dump(mode="json"))
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
#     room_uuid = response.json()
#     return room_uuid

async def add_room(
    room: Room,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    response = await property_service_client.post(f"/room", json = room.model_dump(mode="json"))
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    room_uuid = response.json()
    return room_uuid

async def delete_room(
    room_uuid: UUID,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    response = await property_service_client.delete(f"/room/{str(room_uuid)}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return room_uuid


async def delete_property(
    property_uuid: UUID,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    response = await property_service_client.delete(f"/property/{str(property_uuid)}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return property_uuid


async def change_booking_status(
    booking_uuid: UUID,
    booking_status: BookingStatus,
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> Booking:
    response = await booking_service_client.patch("/booking", json={"booking_uuid":str(booking_uuid), "status": booking_status.value})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    response = response.json()
    return Booking(**response)

async def get_bookings(
    property_uuid: UUID,
    check_in: datetime,
    check_out: datetime,
    property_service_client: AsyncClient = Depends(get_property_service_client),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> list[Availability]:
    
    property_response = await property_service_client.get(f"/property/{str(property_uuid)}")
    if property_response.status_code != 200:
        raise HTTPException(status_code=property_response.status_code, detail=property_response.text)

    property_response = property_response.json()
    property_obj = Property(**property_response)

    availabilities = []

    rooms_response = await property_service_client.get(f"/rooms/{str(property_obj.uuid)}")
    if rooms_response.status_code != 200:
        raise HTTPException(status_code=rooms_response.status_code, detail=rooms_response.text)
    rooms_response = rooms_response.json()
    rooms = [Room(**room) for room in rooms_response]
    params = {
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat()
    }
    for room in rooms:
        params["room_uuid"] = str(room.uuid)
        bookings_response = await booking_service_client.get(f"/bookings", params=params)
        if bookings_response.status_code != 200:
            raise HTTPException(status_code=bookings_response.status_code, detail=bookings_response.text)
        bookings_response=bookings_response.json()
        availability = Availability(**room.model_dump(mode="json"))
        availability.property=property_obj
        availability.bookings = [Booking(**booking) for booking in bookings_response]
        availabilities.append(availability)

    return availabilities


async def get_current_user(
    request: Request,
    user_service_client: AsyncClient = Depends(get_user_service_client),
) -> UserResponse:
    auth = request.headers.get("Authorization", "")
    resp = await user_service_client.get("/me", headers={"Authorization": auth}, timeout=10.0)
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
        f"/user/{str(current_user_uuid)}",
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
    resp = await review_service_client.get(f"/reviews/{str(property_uuid)}", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    reviews_response = resp.json() or []
    return [Review(**review) for review in reviews_response]
