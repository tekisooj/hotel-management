import { Room } from "./Room";

export interface PropertyDetail{
    uuid?: string;
    userUuid: string;
    name: string;
    description?: string;
    country: string;
    state?: string;
    city: string;
    county?: string;
    address: string;
    fullAddress?: string;
    latitude?: number;
    longitude?: number;
    createdAt?: Date;
    updatedAt?: Date;
    rooms?: Room[];
    averageRating?: number;
    stars: number;
    placeId?: number;
}