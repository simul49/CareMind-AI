<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api, fmtTime } from "@/services/api";

const router = useRouter();
const items = ref<any[]>([]);
const loading = ref(true);
const error = ref("");

const severityDot = (sev: string) =>
  sev === "critical" ? "bg-rose" : sev === "warning" ? "bg-amber" : "bg-teal";

onMounted(async () => {
  try {
    const res = await api("/notifications");
    items.value = res.items;
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});

async function open(n: any) {
  if (n.type === "insight" && !n.is_read) {
    const id = Number(n.id.split("-")[1]);
    try {
      await api(`/ai/insights/${id}/read`, { method: "POST" });
      n.is_read = true;
    } catch (e) {
      /* ignore */
    }
  }
  router.push(n.link || "/app/home");
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="text-2xl font-extrabold">Notifications</h2>
      <p class="text-sm text-ink/60">Everything that needs your attention, in one place.</p>
    </div>

    <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>
    <div v-if="loading" class="py-16 text-center text-ink/50">Loading…</div>

    <div v-else-if="!items.length" class="card py-10 text-center">
      <p class="font-extrabold text-lg">You're all caught up</p>
      <p class="mt-1 text-ink/60">No notifications right now.</p>
    </div>

    <div v-for="n in items" :key="n.id">
      <button
        class="card flex w-full items-center gap-4 text-left transition hover:shadow-card"
        :class="{ 'border-l-8 border-rose': n.severity === 'critical' }"
        @click="open(n)"
      >
        <span class="relative grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-teal-light text-sm font-extrabold text-teal-dark">
          {{ n.icon }}
          <span v-if="n.severity === 'critical'" class="absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full bg-rose animate-pulse"></span>
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 shrink-0 rounded-full" :class="n.is_read ? 'bg-ink/15' : severityDot(n.severity)"></span>
            <p class="truncate font-extrabold">{{ n.title }}</p>
          </div>
          <p class="mt-0.5 line-clamp-2 text-sm leading-relaxed text-ink/70">{{ n.content }}</p>
          <p class="mt-1 text-xs font-bold text-ink/40">{{ fmtTime(n.time) }}</p>
        </div>
        <span class="text-ink/30">›</span>
      </button>
    </div>
  </div>
</template>
