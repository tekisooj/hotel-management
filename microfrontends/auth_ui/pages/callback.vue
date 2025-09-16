<template>
  <div>Redirecting...</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { userManager } from "~/api/authClient";
import { useUserStore } from "~/stores/user";
import type { User } from "~/types/User";

onMounted(async () => {
  const store = useUserStore();
  const user = await userManager.signinCallback();

  const res = await $fetch<User>("/me", {
    baseURL: "https://api.example.com", // user-service URL
    headers: { Authorization: `Bearer ${user.id_token}` },
  });

  store.setUser(res, user.id_token);

  if (res.user_type === "guest") {
    window.location.href = "https://guest.example.com";
  } else if (res.user_type === "staff") {
    window.location.href = "https://host.example.com";
  }
});
</script>
