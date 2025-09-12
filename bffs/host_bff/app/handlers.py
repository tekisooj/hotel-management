from datetime import datetime
from uuid import UUID
from fastapi import Depends, HTTPException, Request
from httpx import AsyncClient, HTTPError
from jose import jwt
import httpx

from app.models.review import Review
from app.models.booking import Booking, BookingStatus
from app.models.user import UserResponse, UserUpdate
from bffs.host_bff.app.models.property import Amenity, Property, PropertyDetail, Room
from bffs.host_bff.app.models.property import Availability
from services.user_service.app.models import User


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

def get_event_bus(request: Request):
    return request.app.state.event_bus


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
#     prop = Property(**property.model_dump())
#     response = await property_service_client.post(f"/property", json = prop.model_dump())
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
#     prop_uuid = response.json()

#     if not property.rooms:
#         return prop_uuid
    
#     for room in property.rooms:
        
#         response = await property_service_client.post(f"/room", json = room.model_dump())
#         if response.status_code != 200:
#             raise HTTPException(status_code=response.status_code, detail=response.text)

#     return prop_uuid

async def put_property(
    property: PropertyDetail,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    prop = Property(**property.model_dump())
    response = await property_service_client.post(f"/property", json = prop.model_dump())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    prop_uuid = response.json()

    if not property.rooms:
        return prop_uuid
    
    for room in property.rooms:
        
        response = await property_service_client.post(f"/room", json = room.model_dump())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    return prop_uuid

# async def add_room(
#     room: Room,
#     property_service_client: AsyncClient = Depends(get_property_service_client)
# ) -> UUID:
#     response = await property_service_client.post(f"/room", json = room.model_dump())
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
#     room_uuid = response.json()
#     return room_uuid

async def put_room(
    room: Room,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    response = await property_service_client.put(f"/room", json = room.model_dump())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    room_uuid = response.json()
    return room_uuid

async def delete_user_room(
    room_uuid: UUID,
    property_service_client: AsyncClient = Depends(get_property_service_client)
) -> UUID:
    response = await property_service_client.delete(f"/room/{str(room_uuid)}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return room_uuid


async def delete_user_property(
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
        availability = Availability(**room.model_dump())
        availability.property=property_obj
        availability.bookings = [Booking(**booking) for booking in bookings_response]
        availabilities.append(availability)

    return availabilities


async def cancel_user_booking(
    booking_uuid: UUID,
    current_user_uuid: UUID = Depends(get_current_user_uuid),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
) -> UUID:
    resp = await booking_service_client.patch(
        f"/booking/{str(booking_uuid)}/cancel",
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


async def get_user_reviews(
    user_uuid: UUID,
    review_service_client: AsyncClient = Depends(get_review_service_client),
) -> list[Review]:
    resp = await review_service_client.get(f"/reviews/{str(user_uuid)}", timeout=10.0)
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
    rating_above: float | None = None,
    review_service_client: AsyncClient = Depends(get_review_service_client),
    booking_service_client: AsyncClient = Depends(get_booking_service_client),
    property_service_client: AsyncClient = Depends(get_property_service_client),
):
    properties = []
    if country and city:
        params = {"country": country, "city": city}
        if state:
            params["state"] = state
        property_response = await property_service_client.get("/properties/city", params=params, timeout=10.0)
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
        rooms_result = await property_service_client.get("/rooms", params=params, timeout=10.0)
        if rooms_result.status_code != 200:
            raise HTTPException(status_code=rooms_result.status_code, detail=rooms_result.text)
        rooms_result = rooms_result.json()
        prop_detail = PropertyDetail(**property.model_dump())
        prop_detail.rooms = [Room(**room) for room in rooms_result]
        room_results.append(prop_detail)


    available_room_entries: list[PropertyDetail] = []
    for prop in room_results:
        property_detail = PropertyDetail(**prop.model_dump())
        if not prop.rooms:
            continue
        for room in prop.rooms:
            if check_in_date and check_out_date:
                avail_response = await booking_service_client.get(
                    "/availability",
                    params={
                        "room_uuid": str(room.uuid),
                        "check_in": check_in_date.isoformat(),
                        "check_out": check_out_date.isoformat(),
                    },
                    timeout=10.0,
                )
                if avail_response.status_code != 200:
                    raise HTTPException(status_code=avail_response.status_code, detail=avail_response.text)
                if bool(avail_response.json()):
                    property_detail.rooms.append(room) # type: ignore
        if property_detail.rooms:
            available_room_entries.append(property_detail)
                

    
    for prop_detail in available_room_entries:
        rev = await review_service_client.get(f"/reviews/{str(prop_detail.uuid)}", timeout=10.0)
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
