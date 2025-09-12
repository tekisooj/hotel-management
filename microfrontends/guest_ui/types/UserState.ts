import { User } from "./User"

export interface UserState {
  token: string | null
  uuid: string | null
  profile: User | null
}