export interface Review{
    uuid: string;
    propertyUuid: string;
    userUuid: string;
    rating: number
    commet: string;
    timestamp?: string;
}