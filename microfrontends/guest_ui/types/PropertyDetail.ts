import { Room } from "./Room";

export interface PropertyDetail{
    uuid?: string;
    user_uuid: string;
    name: string;
    description?: string;
    country: string;
    state?: string;
    city: string;
    county?: string;
    address: string;
    full_address?: string;
    latitude?: number;
    longitude?: number;
    created_at?: Date;
    updated_at?: Date;
    rooms?: Room[];
    average_rating?: number;
}