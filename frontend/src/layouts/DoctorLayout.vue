<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();
const tabs = [
  { path: "/app/doctor", label: "Patients", icon: "🩺" },
  { path: "/app/profile", label: "Me", icon: "👤" },
];
</script>

<template>
  <div class="min-h-screen bg-cream font-nunito text-ink">
    <!-- Top bar -->
    <header class="sticky top-0 z-30 border-b border-ink/5 bg-cream/80 backdrop-blur">
      <div class="mx-auto flex max-w-lg items-center justify-between px-5 py-4">
        <div class="flex items-center gap-2">
          <span class="grid h-9 w-9 place-items-center rounded-xl bg-teal text-lg text-white">🩺</span>
          <div>
            <p class="text-sm font-extrabold leading-tight">CareMind</p>
            <p class="text-[0.7rem] font-bold text-teal-dark">Doctor Portal</p>
          </div>
        </div>
        <RouterLink to="/app/notifications" class="grid h-10 w-10 place-items-center rounded-2xl bg-white text-lg shadow-card">
          🔔
        </RouterLink>
      </div>
    </header>

    <main class="mx-auto max-w-lg px-5 pb-28 pt-5">
      <RouterView />
    </main>

    <!-- Bottom nav -->
    <nav class="fixed bottom-0 left-0 right-0 z-30 border-t border-ink/5 bg-white/95 backdrop-blur">
      <div class="mx-auto flex max-w-lg">
        <RouterLink
          v-for="t in tabs"
          :key="t.path"
          :to="t.path"
          class="flex flex-1 flex-col items-center gap-0.5 py-3 text-xs font-extrabold"
          :class="$route.path === t.path ? 'text-teal-dark' : 'text-ink/40'"
        >
          <span class="text-xl">{{ t.icon }}</span>
          {{ t.label }}
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
