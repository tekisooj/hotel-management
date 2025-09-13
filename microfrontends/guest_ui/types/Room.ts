import { Amenity } from "./Amenity";
import { RoomType } from "./RoomType";

export interface Room{
    uuid: string;
    property_uuid: string;
    name: string;
    description: string;
    capacity: number;
    room_type: RoomType;
    price_per_night: number;
    min_price_per_night: number;
    max_price_per_night: number;
    created_at?: Date;
    updated_at?: Date;
    amenities?: Amenity[];

}