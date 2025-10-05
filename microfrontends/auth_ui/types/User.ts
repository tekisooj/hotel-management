import type { UserType } from "./UserType"

export interface User {
  uuid: string
  name: string
  last_name: string
  email: string
  user_type: UserType
}
