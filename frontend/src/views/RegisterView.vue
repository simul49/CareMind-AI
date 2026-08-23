<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const form = ref({ full_name: "", email: "", password: "", role: "elder" });
const loading = ref(false);
const error = ref("");

const submit = async () => {
  error.value = "";
  loading.value = true;
  try {
    await auth.register(form.value);
    router.push("/app/home");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-gradient-to-b from-teal-light via-cream to-amber-light/40 px-5 py-10">
    <div class="w-full max-w-md">
      <button class="mb-6 text-teal-dark font-bold" @click="router.push('/')">← Back to home</button>
      <div class="card p-8">
        <h1 class="text-3xl font-extrabold">Join CareMind</h1>
        <p class="mt-1 text-ink/60">Set up your account — it takes a minute.</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="label">Full name</label>
            <input v-model="form.full_name" class="input mt-1" placeholder="Your name" required />
          </div>
          <div>
            <label class="label">Email</label>
            <input v-model="form.email" type="email" class="input mt-1" placeholder="you@example.com" required />
          </div>
          <div>
            <label class="label">Password</label>
            <input v-model="form.password" type="password" class="input mt-1" placeholder="8+ characters" minlength="8" required />
          </div>
          <div>
            <label class="label">I am a…</label>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'elder' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'elder'">Older adult</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'family' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'family'">Family</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'doctor' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'doctor'">Doctor</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'caregiver' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'caregiver'">Caregiver</button>
            </div>
          </div>

          <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? "Creating…" : "Create account" }}
          </button>
        </form>

        <p class="mt-6 text-center text-ink/60">
          Already have one?
          <button class="font-extrabold text-teal" @click="router.push('/login')">Sign in</button>
        </p>
      </div>
    </div>
  </div>
</template>
