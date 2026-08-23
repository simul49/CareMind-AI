<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "@/i18n";
import LangSwitcher from "@/components/LangSwitcher.vue";

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

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
      <div class="mb-6 flex items-center justify-between">
        <button class="text-teal-dark font-bold" @click="router.push('/')">{{ t("auth.backHome") }}</button>
        <LangSwitcher />
      </div>
      <div class="card p-8">
        <div class="grid h-14 w-14 place-items-center rounded-2xl bg-teal text-sm font-extrabold text-white shadow-soft">CM</div>
        <h1 class="mt-4 text-3xl font-extrabold">{{ t("auth.loginTitle") }}</h1>
        <p class="mt-1 text-ink/60">{{ t("auth.loginSub") }}</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="label">{{ t("auth.email") }}</label>
            <input v-model="email" type="email" class="input mt-1" placeholder="you@example.com" autocomplete="email" />
          </div>
          <div>
            <label class="label">{{ t("auth.password") }}</label>
            <input v-model="password" type="password" class="input mt-1" placeholder="••••••••" autocomplete="current-password" />
          </div>

          <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? t("auth.signingIn") : t("auth.signIn") }}
          </button>
        </form>

        <p class="mt-6 text-center text-ink/60">
          {{ t("auth.newHere") }}
          <button class="font-extrabold text-teal" @click="router.push('/register')">{{ t("auth.signUp") }}</button>
        </p>
      </div>
    </div>
  </div>
</template>
