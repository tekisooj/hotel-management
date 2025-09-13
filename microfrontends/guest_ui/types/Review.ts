export interface Review{
    uuid: string;
    property_uuid: string;
    user_uuid: string;
    rating: number
    commet: string;
    timestamp?: string;
}