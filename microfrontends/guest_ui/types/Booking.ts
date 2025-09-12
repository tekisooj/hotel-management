import { BookingStatus } from "./BookingStatus"

export interface Booking {
    uuid: string;
    user_uuid: string;
    room_uuid: string;
    check_in: Date;
    check_out: Date;
    total_price: number;
    status: BookingStatus;
    created_at: Date;
    updated_at: Date;
}