<template>
  <div>
    <h2>Create Account</h2>
    <form @submit.prevent="signup">
      <input v-model="form.name" placeholder="First Name" required />
      <input v-model="form.last_name" placeholder="Last Name" required />
      <input v-model="form.email" type="email" placeholder="Email" required />
      <input v-model="form.password" type="password" placeholder="Password" required />

      <select v-model="form.user_type">
        <option value="guest">Guest</option>
        <option value="staff">Host</option>
      </select>

      <button type="submit">Register</button>
    </form>
    <p v-if="error" style="color:red">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { useRuntimeConfig } from "nuxt/app";
import { ref } from "vue";
import type { UserType } from "~/types/UserType";

const form = ref({
  name: "",
  last_name: "",
  email: "",
  password: "",
  user_type: "guest" as UserType,
});

const error = ref("");
const config = useRuntimeConfig()

async function signup() {
  try {
    await $fetch("/user", {
      method: "POST",
      baseURL: config.public.userApiBase,
      body: form.value,
    });

    window.location.href = "/";
  } catch (e: any) {
    error.value = e.data?.message || e.message;
  }
}
</script>
