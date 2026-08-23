<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const accessible = ref(auth.user?.is_accessible_mode ?? false);

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
        {{ auth.user?.role }}
      </span>
    </div>

    <div class="card flex items-center justify-between">
      <div>
        <p class="font-extrabold">Big & easy mode</p>
        <p class="text-sm text-ink/60">Larger text and buttons</p>
      </div>
      <button class="h-9 w-16 rounded-full p-1 transition" :class="accessible ? 'bg-teal' : 'bg-ink/15'" @click="accessible = !accessible">
        <span class="block h-7 w-7 rounded-full bg-white shadow transition-transform" :class="accessible ? 'translate-x-7' : ''"></span>
      </button>
    </div>

    <div class="card">
      <p class="font-extrabold">About CareMind</p>
      <p class="mt-1 text-ink/60 text-sm leading-relaxed">
        CareMind AI connects older adults, family, doctors and an AI companion — keeping
        everyone in the loop while protecting privacy. CareMind never diagnoses or prescribes.
      </p>
    </div>

    <button class="btn w-full border-2 border-rose/20 bg-rose/5 py-4 text-lg font-extrabold text-rose" @click="logout">
      Sign out
    </button>
  </div>
</template>
