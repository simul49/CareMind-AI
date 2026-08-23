<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

const submit = async () => {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value.trim(), password.value);
    router.push(auth.user?.role === "doctor" ? "/app/doctor" : "/app/home");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-gradient-to-b from-teal-light via-cream to-amber-light/40 px-5">
    <div class="w-full max-w-md">
      <button class="mb-6 text-teal-dark font-bold" @click="router.push('/')">← Back to home</button>
      <div class="card p-8">
        <div class="grid h-14 w-14 place-items-center rounded-2xl bg-teal text-sm font-extrabold text-white shadow-soft">CM</div>
        <h1 class="mt-4 text-3xl font-extrabold">Welcome back</h1>
        <p class="mt-1 text-ink/60">Sign in to your care circle.</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="label">Email</label>
            <input v-model="email" type="email" class="input mt-1" placeholder="you@example.com" autocomplete="email" />
          </div>
          <div>
            <label class="label">Password</label>
            <input v-model="password" type="password" class="input mt-1" placeholder="••••••••" autocomplete="current-password" />
          </div>

          <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? "Signing in…" : "Sign in" }}
          </button>
        </form>

        <p class="mt-6 text-center text-ink/60">
          New here?
          <button class="font-extrabold text-teal" @click="router.push('/register')">Create an account</button>
        </p>
      </div>
    </div>
  </div>
</template>
