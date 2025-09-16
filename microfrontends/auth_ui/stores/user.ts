import { defineStore } from "pinia";
import type { UserState } from "~/types/UserState";
import type { User } from "~/types/User";

export const useUserStore = defineStore("user", {
  state: (): UserState => ({
    currentUser: null,
    token: null,
    uuid: null,
    profile: null
  }),

  actions: {
    setUser(user: User, token: string) {
      this.currentUser = user;
      this.token = token;
    },
    clearUser() {
      this.currentUser = null;
      this.token = null;
    },
  },
});
