<template>
  <div>
    <h2>Welcome to Hotel Management App</h2>
    <button @click="login">Sign In</button>
    <NuxtLink to="/signup">Create Account</NuxtLink>
  </div>
</template>

<script setup lang="ts">
import { userManager } from "~/api/authClient";

async function login() {
  await userManager.signinRedirect();
}
</script>