import { Amenity } from "./Amenity";
import { Image } from "./Image";
import { RoomType } from "./RoomType";

export interface Room{
    uuid: string;
    propertyUuid: string;
    name: string;
    description: string;
    capacity: number;
    roomType: RoomType;
    pricePerNight: number;
    minPricePerNight: number;
    maxPricePerNight: number;
    createdAt?: Date;
    updatedAt?: Date;
    amenities?: Amenity[];
    images?: Image[];

}
