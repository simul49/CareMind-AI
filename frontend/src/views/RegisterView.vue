<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "@/i18n";
import LangSwitcher from "@/components/LangSwitcher.vue";

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

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
      <div class="mb-6 flex items-center justify-between">
        <button class="text-teal-dark font-bold" @click="router.push('/')">{{ t("auth.backHome") }}</button>
        <LangSwitcher />
      </div>
      <div class="card p-8">
        <h1 class="text-3xl font-extrabold">{{ t("auth.joinTitle") }}</h1>
        <p class="mt-1 text-ink/60">{{ t("auth.joinSub") }}</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="label">{{ t("auth.name") }}</label>
            <input v-model="form.full_name" class="input mt-1" :placeholder="t('auth.namePh')" required />
          </div>
          <div>
            <label class="label">{{ t("auth.email") }}</label>
            <input v-model="form.email" type="email" class="input mt-1" placeholder="you@example.com" required />
          </div>
          <div>
            <label class="label">{{ t("auth.password") }}</label>
            <input v-model="form.password" type="password" class="input mt-1" :placeholder="t('auth.passPh')" minlength="8" required />
          </div>
          <div>
            <label class="label">{{ t("auth.role") }}</label>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'elder' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'elder'">{{ t("auth.elder") }}</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'family' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'family'">{{ t("auth.familyRole") }}</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'doctor' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'doctor'">{{ t("auth.doctorRole") }}</button>
              <button type="button" class="rounded-2xl border-2 px-3 py-3 text-lg font-bold transition"
                      :class="form.role === 'caregiver' ? 'border-teal bg-teal-light text-teal-dark' : 'border-ink/10'"
                      @click="form.role = 'caregiver'">{{ t("auth.caregiverRole") }}</button>
            </div>
          </div>

          <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? t("auth.creating") : t("auth.signUp") }}
          </button>
        </form>

        <p class="mt-6 text-center text-ink/60">
          {{ t("auth.alreadyHave") }}
          <button class="font-extrabold text-teal" @click="router.push('/login')">{{ t("auth.signIn") }}</button>
        </p>
      </div>
    </div>
  </div>
</template>
