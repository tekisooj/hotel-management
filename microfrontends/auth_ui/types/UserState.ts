import { User } from "./User"

export interface UserState {
  currentUser: User | null
  token: string | null
  uuid: string | null
  profile: User | null
}