<template>
  <div>
    <button @click="logout">Log out</button>
  </div>
</template>

<script setup lang="ts">
import { signOutRedirect } from "~/api/authClient";
import { useUserStore } from "~/stores/user";

function logout() {
  const store = useUserStore();
  store.clearUser();
  signOutRedirect();
}
</script>
