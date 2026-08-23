<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "@/i18n";

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const accessible = ref(auth.user?.is_accessible_mode ?? false);

const roleKey = (r?: string) =>
  r === "elder" ? "auth.elder"
  : r === "family" ? "auth.familyRole"
  : r === "doctor" ? "auth.doctorRole"
  : r === "caregiver" ? "auth.caregiverRole"
  : "";

const logout = () => {
  auth.logout();
  router.push("/");
};
</script>

<template>
  <div class="space-y-5">
    <div class="card text-center">
      <div class="mx-auto grid h-20 w-20 place-items-center rounded-full bg-teal text-3xl font-extrabold text-white">
        {{ auth.user?.full_name.split(" ").map((s) => s[0]).slice(0, 2).join("") }}
      </div>
      <h2 class="mt-3 text-2xl font-extrabold">{{ auth.user?.full_name }}</h2>
      <p class="text-ink/60">{{ auth.user?.email }}</p>
      <span class="mt-2 inline-block rounded-2xl bg-teal-light px-4 py-1.5 font-bold capitalize text-teal-dark">
        {{ t(roleKey(auth.user?.role)) }}
      </span>
    </div>

    <div class="card flex items-center justify-between">
      <div>
        <p class="font-extrabold">{{ t("prof.bigMode") }}</p>
        <p class="text-sm text-ink/60">{{ t("prof.bigModeSub") }}</p>
      </div>
      <button class="h-9 w-16 rounded-full p-1 transition" :class="accessible ? 'bg-teal' : 'bg-ink/15'" @click="accessible = !accessible">
        <span class="block h-7 w-7 rounded-full bg-white shadow transition-transform" :class="accessible ? 'translate-x-7' : ''"></span>
      </button>
    </div>

    <div class="card">
      <p class="font-extrabold">{{ t("prof.about") }}</p>
      <p class="mt-1 text-ink/60 text-sm leading-relaxed">{{ t("prof.aboutText") }}</p>
    </div>

    <button class="btn w-full border-2 border-rose/20 bg-rose/5 py-4 text-lg font-extrabold text-rose" @click="logout">
      {{ t("prof.signOut") }}
    </button>
  </div>
</template>
