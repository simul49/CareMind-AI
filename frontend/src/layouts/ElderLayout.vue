<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const tabs = [
  { name: "home", label: "Home", emoji: "🏠" },
  { name: "health", label: "Health", emoji: "❤️" },
  { name: "ai", label: "CareMind", emoji: "🤖" },
  { name: "moments", label: "Moments", emoji: "👨‍👩‍👧" },
  { name: "profile", label: "Me", emoji: "👤" },
];

const activeTab = computed(() => route.name as string);
const pageTitle = computed(() => tabs.find((t) => t.name === activeTab.value)?.label || "");

const initials = computed(() =>
  (auth.user?.full_name || "U").split(" ").map((s) => s[0]).slice(0, 2).join(""),
);
</script>

<template>
  <div class="mx-auto min-h-screen max-w-lg pb-28">
    <!-- Header -->
    <header class="sticky top-0 z-20 flex items-center justify-between bg-cream/90 px-5 py-4 backdrop-blur">
      <div class="flex items-center gap-3">
        <div class="grid h-12 w-12 place-items-center rounded-2xl bg-teal font-extrabold text-white shadow-soft">
          {{ initials }}
        </div>
        <div>
          <p class="text-sm font-bold text-teal-dark">{{ pageTitle }}</p>
          <p class="text-lg font-extrabold leading-tight">{{ auth.user?.full_name }}</p>
        </div>
      </div>
      <button class="rounded-2xl bg-white px-4 py-2 text-lg shadow-card" title="Notifications">🔔</button>
    </header>

    <!-- Main -->
    <main class="px-5 pt-4">
      <router-view v-slot="{ Component }">
        <transition name="pop" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- SOS floating button -->
    <button
      class="pulse-sos fixed bottom-24 right-5 z-30 grid h-16 w-16 place-items-center rounded-full bg-rose text-3xl text-white shadow-soft"
      title="SOS — Emergency"
      @click="router.push('/app/emergency')"
    >
      🛟
    </button>

    <!-- Bottom nav -->
    <nav
      class="fixed bottom-0 left-0 right-0 z-20 border-t border-ink/5 bg-white/95 backdrop-blur"
      style="padding-bottom: env(safe-area-inset-bottom)"
    >
      <div class="mx-auto flex max-w-lg items-stretch justify-around">
        <button
          v-for="t in tabs"
          :key="t.name"
          class="flex flex-1 flex-col items-center gap-0.5 py-3 transition"
          :class="activeTab === t.name ? 'text-teal-dark' : 'text-ink/45'"
          @click="router.push('/app/' + t.name)"
        >
          <span class="text-2xl" :class="{ 'scale-110': activeTab === t.name }">{{ t.emoji }}</span>
          <span class="text-xs font-bold">{{ t.label }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>
