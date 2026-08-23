<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();
</script>

<template>
  <div class="min-h-screen bg-cream font-nunito text-ink">
    <header class="sticky top-0 z-20 border-b border-ink/5 bg-cream/90 backdrop-blur">
      <div class="mx-auto flex max-w-lg items-center gap-3 px-5 py-4">
        <button class="grid h-10 w-10 place-items-center rounded-2xl bg-white text-lg shadow-card" @click="router.back()">
          ←
        </button>
        <p class="text-lg font-extrabold">Notifications</p>
      </div>
    </header>
    <main class="mx-auto max-w-lg px-5 py-5">
      <RouterView />
    </main>
  </div>
</template>
