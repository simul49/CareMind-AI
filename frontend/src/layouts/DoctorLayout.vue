<script setup lang="ts">
import { useRouter } from "vue-router";
import { useI18n } from "@/i18n";
import LangSwitcher from "@/components/LangSwitcher.vue";

const router = useRouter();
const { t } = useI18n();
const tabs = [
  { path: "/app/doctor", labelKey: "nav.patients" },
  { path: "/app/profile", labelKey: "nav.me" },
];
</script>

<template>
  <div class="min-h-screen bg-cream font-nunito text-ink">
    <!-- Top bar -->
    <header class="sticky top-0 z-30 border-b border-ink/5 bg-cream/80 backdrop-blur">
      <div class="mx-auto flex max-w-lg items-center justify-between px-5 py-4">
        <div class="flex items-center gap-2">
          <span class="grid h-9 w-9 place-items-center rounded-xl bg-teal text-xs font-extrabold text-white">CM</span>
          <div>
            <p class="text-sm font-extrabold leading-tight">CareMind</p>
            <p class="text-[0.7rem] font-bold text-teal-dark">{{ t("doc.portal") }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <LangSwitcher />
          <RouterLink to="/app/notifications" class="rounded-2xl bg-white px-4 py-2.5 text-sm font-extrabold shadow-card">
            {{ t("nav.alerts") }}
          </RouterLink>
        </div>
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
          class="mx-1 flex-1 rounded-2xl px-1 py-2.5 text-sm font-extrabold"
          :class="
            $route.path === t.path
              ? 'bg-teal text-white shadow-soft'
              : 'text-ink/50 hover:bg-teal/10'
          "
        >
          {{ t(t.labelKey) }}
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
