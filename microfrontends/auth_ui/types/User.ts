import { UserType } from "./UserType";

export interface User{
    uuid: string;
    name: string;
    lastName: string;
    email: string;
    userType: UserType;
}