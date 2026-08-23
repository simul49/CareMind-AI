<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { api } from "@/services/api";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const badgeCount = ref(0);
let badgeTimer: ReturnType<typeof setInterval> | null = null;

const refreshBadge = async () => {
  try {
    const res = await api("/notifications");
    badgeCount.value = res.items.filter(
      (n: any) => n.severity === "critical" || (n.type === "insight" && !n.is_read),
    ).length;
  } catch {
    badgeCount.value = 0;
  }
};

onMounted(() => {
  refreshBadge();
  badgeTimer = setInterval(refreshBadge, 30000);
});
onUnmounted(() => {
  if (badgeTimer) clearInterval(badgeTimer);
});

const roleTabs: Record<string, { name: string; label: string }[]> = {
  elder: [
    { name: "home", label: "Home" },
    { name: "health", label: "Health" },
    { name: "ai", label: "CareMind" },
    { name: "moments", label: "Moments" },
    { name: "profile", label: "Me" },
  ],
  family: [
    { name: "home", label: "Home" },
    { name: "chat", label: "Chat" },
    { name: "moments", label: "Moments" },
    { name: "profile", label: "Me" },
  ],
  caregiver: [
    { name: "home", label: "Home" },
    { name: "chat", label: "Chat" },
    { name: "moments", label: "Moments" },
    { name: "profile", label: "Me" },
  ],
};

const tabs = computed(() => roleTabs[auth.user?.role as string] || roleTabs.elder);
const isElder = computed(() => auth.user?.role === "elder");

const activeTab = computed(() => route.name as string);
const pageTitle = computed(() => tabs.value.find((t) => t.name === activeTab.value)?.label || "");

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
      <RouterLink
        to="/notifications"
        class="relative rounded-2xl bg-white px-4 py-2.5 text-sm font-extrabold text-ink shadow-card"
        title="Alerts"
      >
        Alerts
        <span
          v-if="badgeCount > 0"
          class="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-rose px-1 text-[0.65rem] font-extrabold text-white"
        >{{ badgeCount > 9 ? "9+" : badgeCount }}</span>
      </RouterLink>
    </header>

    <!-- Main -->
    <main class="px-5 pt-4">
      <router-view v-slot="{ Component }">
        <transition name="pop" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- SOS floating button (elder only) -->
    <button
      v-if="isElder"
      class="pulse-sos fixed bottom-24 right-5 z-30 grid h-16 w-16 place-items-center rounded-full bg-rose text-lg font-extrabold tracking-wide text-white shadow-soft"
      title="SOS — Emergency"
      @click="router.push('/app/emergency')"
    >
      SOS
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
          class="mx-1 flex-1 rounded-2xl px-1 py-2.5 text-sm font-extrabold transition"
          :class="
            activeTab === t.name
              ? 'bg-teal text-white shadow-soft'
              : 'text-ink/50 hover:bg-teal/10'
          "
          @click="router.push('/app/' + t.name)"
        >
          {{ t.label }}
        </button>
      </div>
    </nav>
  </div>
</template>
