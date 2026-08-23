<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, fmtDay } from "@/services/api";

const route = useRoute();
const router = useRouter();
const patientId = Number(route.params.id);

const summary = ref<any>(null);
const loading = ref(true);
const error = ref("");
const saving = ref(false);
const saved = ref("");

const form = ref({ title: "", description: "", instructions: "" });

// ---- BP chart ----
const W = 320;
const H = 130;
const PAD_X = 16;
const PAD_Y = 16;
const Y_MIN = 50;
const Y_MAX = 190;

const bpSeries = computed(() =>
  (summary.value?.timeline || [])
    .filter((m: any) => m.metric_type === "blood_pressure" && m.values?.systolic)
    .sort((a: any, b: any) => a.measured_at.localeCompare(b.measured_at))
    .map((m: any) => ({ t: m.measured_at, s: m.values.systolic, d: m.values.diastolic })),
);

const bpPoints = computed(() => {
  const rows = bpSeries.value;
  if (!rows.length) return { s: "", d: "", labels: [] as string[] };
  const n = rows.length;
  const x = (i: number) => (n === 1 ? W / 2 : PAD_X + (i * (W - 2 * PAD_X)) / (n - 1));
  const y = (v: number) => H - PAD_Y - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * (H - 2 * PAD_Y);
  return {
    s: rows.map((r, i) => `${x(i).toFixed(1)},${y(r.s).toFixed(1)}`).join(" "),
    d: rows.map((r, i) => `${x(i).toFixed(1)},${y(r.d).toFixed(1)}`).join(" "),
    labels: [fmtDay(rows[0].t), fmtDay(rows[rows.length - 1].t)],
  };
});

const bpLatest = computed(() => {
  const rows = bpSeries.value;
  return rows.length ? rows[rows.length - 1] : null;
});

const severityStyle = (sev: string) =>
  sev === "critical"
    ? "border-l-4 border-rose bg-rose/5"
    : sev === "warning"
      ? "border-l-4 border-amber bg-amber-light/40"
      : "border-l-4 border-teal bg-teal-light/40";

const severityTag = (sev: string) =>
  sev === "critical" ? "bg-rose text-white" : sev === "warning" ? "bg-amber text-white" : "bg-teal-light text-teal-dark";

onMounted(async () => {
  try {
    summary.value = await api(`/doctors/patients/${patientId}/summary`);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});

async function createPlan() {
  saved.value = "";
  if (!form.value.title.trim()) return;
  saving.value = true;
  try {
    await api("/doctors/care-plans", {
      method: "POST",
      body: { elder_user_id: patientId, ...form.value },
    });
    form.value = { title: "", description: "", instructions: "" };
    summary.value = await api(`/doctors/patients/${patientId}/summary`);
    saved.value = "Care plan sent — Rahima and her family can see it right away. ✅";
  } catch (e: any) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="space-y-5">
    <button class="flex items-center gap-1 text-sm font-extrabold text-teal-dark" @click="router.push('/app/doctor')">
      ← Back to patients
    </button>

    <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>
    <div v-if="loading" class="py-16 text-center text-ink/50">Loading…</div>

    <template v-else-if="summary">
      <div class="flex items-center gap-4">
        <span class="grid h-16 w-16 place-items-center rounded-3xl bg-teal text-3xl text-white">
          {{ summary.patient.name?.charAt(0) }}
        </span>
        <div>
          <h2 class="text-2xl font-extrabold">{{ summary.patient.name }}</h2>
          <p class="text-sm text-ink/60">CareMind patient · real-time insights</p>
        </div>
      </div>

      <!-- BP trend -->
      <div class="card">
        <div class="mb-1 flex items-center justify-between">
          <h3 class="font-extrabold">Blood pressure trend</h3>
          <span v-if="bpLatest" class="rounded-xl bg-teal-light px-3 py-1 text-sm font-extrabold text-teal-dark">
            {{ bpLatest.s }}/{{ bpLatest.d }} mmHg
          </span>
        </div>
        <svg v-if="bpSeries.length" :viewBox="`0 0 ${W} ${H}`" class="w-full">
          <!-- grid -->
          <g stroke="#e8e9e0">
            <line v-for="v in [80, 120, 160]" :key="v" x1="0" :x2="W" :y1="H - PAD_Y - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * (H - 2 * PAD_Y)" :y2="H - PAD_Y - ((v - Y_MIN) / (Y_MAX - Y_MIN)) * (H - 2 * PAD_Y)" />
          </g>
          <!-- normal band 90-140 -->
          <rect x="0" :y="H - PAD_Y - ((140 - Y_MIN) / (Y_MAX - Y_MIN)) * (H - 2 * PAD_Y)" :width="W" :height="((140 - 90) / (Y_MAX - Y_MIN)) * (H - 2 * PAD_Y)" fill="#2d8f88" opacity="0.08" />
          <!-- diastolic -->
          <polyline :points="bpPoints.d" fill="none" stroke="#d9a441" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
          <!-- systolic -->
          <polyline :points="bpPoints.s" fill="none" stroke="#2d8f88" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />
          <!-- labels -->
          <text x="0" :y="H - 3" font-size="8" fill="#8a8f86">{{ bpPoints.labels[0] }}</text>
          <text :x="W - 40" :y="H - 3" font-size="8" fill="#8a8f86">{{ bpPoints.labels[1] }}</text>
          <text x="0" y="8" font-size="8" fill="#8a8f86">160</text>
        </svg>
        <div v-else class="py-6 text-center text-sm text-ink/50">No blood pressure readings yet.</div>
        <div class="mt-2 flex gap-4 text-xs font-bold text-ink/50">
          <span><i class="mr-1 inline-block h-2 w-4 rounded-full bg-teal"></i>Systolic</span>
          <span><i class="mr-1 inline-block h-2 w-4 rounded-full bg-amber"></i>Diastolic</span>
          <span class="ml-auto">Reference band 90–140</span>
        </div>
      </div>

      <!-- Medicines -->
      <div class="card">
        <h3 class="mb-3 font-extrabold">Prescribed medicines</h3>
        <div v-if="summary.medicines.length" class="space-y-2">
          <div v-for="m in summary.medicines" :key="m.name" class="flex items-center gap-3 rounded-2xl bg-cream px-4 py-3">
            <span class="text-xl">💊</span>
            <div class="flex-1">
              <p class="font-extrabold">{{ m.name }}</p>
              <p class="text-xs text-ink/60">{{ m.dosage }}{{ m.dosage_unit }} · {{ m.frequency }}</p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-ink/50">No active prescriptions.</p>
      </div>

      <!-- Insights -->
      <div class="card">
        <h3 class="mb-3 font-extrabold">CareMind insights</h3>
        <div v-if="summary.insights.length" class="space-y-2">
          <div v-for="(i, idx) in summary.insights" :key="idx" class="rounded-2xl px-4 py-3" :class="severityStyle(i.severity)">
            <div class="flex items-center justify-between gap-2">
              <p class="font-extrabold">{{ i.title }}</p>
              <span class="rounded-lg px-2 py-0.5 text-[0.65rem] font-extrabold uppercase" :class="severityTag(i.severity)">{{ i.severity }}</span>
            </div>
            <p class="mt-1 text-sm leading-relaxed text-ink/70">{{ i.content }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-ink/50">No insights yet.</p>
      </div>

      <!-- Care plans -->
      <div class="card">
        <h3 class="mb-3 font-extrabold">Care plans</h3>
        <div v-if="summary.care_plans.length" class="mb-4 space-y-2">
          <div v-for="p in summary.care_plans" :key="p.id" class="rounded-2xl border border-teal/20 bg-teal-light/30 px-4 py-3">
            <div class="flex items-center justify-between gap-2">
              <p class="font-extrabold">{{ p.title }}</p>
              <span class="rounded-lg bg-teal px-2 py-0.5 text-[0.65rem] font-extrabold text-white">{{ p.status }}</span>
            </div>
            <p v-if="p.description" class="mt-1 text-sm text-ink/70">{{ p.description }}</p>
          </div>
        </div>
        <p v-if="!summary.care_plans.length" class="mb-4 text-sm text-ink/50">No care plans yet — create the first one below.</p>

        <p v-if="saved" class="mb-3 rounded-2xl bg-teal-light px-4 py-3 text-sm font-bold text-teal-dark">{{ saved }}</p>
        <form class="space-y-3" @submit.prevent="createPlan">
          <input v-model="form.title" class="input" placeholder="Title · e.g. Reduce salt & walk daily" required />
          <textarea v-model="form.description" class="input min-h-[72px]" placeholder="Description (optional)"></textarea>
          <textarea v-model="form.instructions" class="input min-h-[72px]" placeholder="Instructions for Rahima & family (optional)"></textarea>
          <button class="btn-primary w-full" :disabled="saving">{{ saving ? "Sending…" : "Send care plan 🩺" }}</button>
        </form>
      </div>
    </template>
  </div>
</template>
