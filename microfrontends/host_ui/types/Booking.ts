import { BookingStatus } from "./BookingStatus"

export interface Booking {
    uuid: string;
    userUuid: string;
    roomUuid: string;
    checkIn: Date;
    checkOut: Date;
    totalPrice: number;
    status: BookingStatus;
    createdAt: Date;
    updatedAt: Date;
}