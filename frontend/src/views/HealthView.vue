<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api, fmtDay, fmtTime } from "@/services/api";

const timeline = ref<any[]>([]);
const loading = ref(true);
const showQuick = ref(false);
const quickType = ref<"bp" | "mood" | "walk">("bp");
const form = ref({ systolic: "", diastolic: "", bpm: "", mood_level: 4, steps: "", note: "" });

const byDay = computed(() => {
  const map: Record<string, any[]> = {};
  for (const m of timeline.value) {
    const day = fmtDay(m.measured_at);
    (map[day] ||= []).push(m);
  }
  return map;
});

onMounted(async () => {
  try {
    timeline.value = await api("/health/timeline?days=14");
  } finally {
    loading.value = false;
  }
});

const labelFor = (t: string) =>
  ({ blood_pressure: "🩺 Blood pressure", heart_rate: "❤️ Heart rate", sleep: "🌙 Sleep",
     activity: "🚶 Activity", mood: "😊 Mood", weight: "⚖️ Weight" }[t] || t);

const valText = (m: any) => {
  const v = m.values;
  if (m.metric_type === "blood_pressure") return `${v.systolic}/${v.diastolic} mmHg`;
  if (m.metric_type === "heart_rate") return `${v.bpm} bpm`;
  if (m.metric_type === "sleep") return `${v.sleep_hours} h`;
  if (m.metric_type === "activity") return `${v.steps?.toLocaleString() ?? ""} steps`;
  if (m.metric_type === "mood") return ["😟", "😔", "😐", "🙂", "😊"][v.mood_level - 1];
  if (m.metric_type === "weight") return `${v.kg} kg`;
  return JSON.stringify(v);
};

const openQuick = (t: "bp" | "mood" | "walk") => {
  quickType.value = t;
  form.value = { systolic: "", diastolic: "", bpm: "", mood_level: 4, steps: "", note: "" };
  showQuick.value = true;
};

const submitQuick = async () => {
  let body: any;
  if (quickType.value === "bp") {
    body = { systolic: +form.value.systolic, diastolic: +form.value.diastolic, pulse: +form.value.bpm || null };
    await api("/health/blood-pressure", { method: "POST", body });
  } else if (quickType.value === "mood") {
    await api("/health/mood", { method: "POST", body: { mood_level: form.value.mood_level, note: form.value.note } });
  } else {
    body = { activity_type: "walk", steps: +form.value.steps || 0, duration_minutes: Math.round((+form.value.steps || 0) / 90) };
    await api("/health/activity", { method: "POST", body });
  }
  showQuick.value = false;
  timeline.value = await api("/health/timeline?days=14");
};
</script>

<template>
  <div class="space-y-5">
    <section>
      <h3 class="text-xl font-extrabold">Quick log</h3>
      <div class="mt-3 grid grid-cols-3 gap-3">
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('bp')">
          <span class="text-4xl">🩺</span><p class="mt-1 font-extrabold">Blood pressure</p>
        </button>
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('mood')">
          <span class="text-4xl">😊</span><p class="mt-1 font-extrabold">Feeling</p>
        </button>
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('walk')">
          <span class="text-4xl">🚶</span><p class="mt-1 font-extrabold">Walk</p>
        </button>
      </div>
    </section>

    <section v-if="showQuick" class="card bg-teal-light/50">
      <template v-if="quickType === 'bp'">
        <h4 class="text-xl font-extrabold">Log blood pressure</h4>
        <div class="mt-3 grid grid-cols-3 gap-3">
          <div><label class="label">Systolic</label><input v-model="form.systolic" type="number" class="input mt-1" placeholder="138" /></div>
          <div><label class="label">Diastolic</label><input v-model="form.diastolic" type="number" class="input mt-1" placeholder="86" /></div>
          <div><label class="label">Pulse</label><input v-model="form.bpm" type="number" class="input mt-1" placeholder="74" /></div>
        </div>
      </template>
      <template v-else-if="quickType === 'mood'">
        <h4 class="text-xl font-extrabold">How do you feel?</h4>
        <div class="mt-3 flex gap-2">
          <button v-for="(e, i) in ['😟', '😔', '😐', '🙂', '😊']" :key="i"
                  class="grid h-14 w-14 place-items-center rounded-2xl bg-white text-3xl"
                  :class="{ 'ring-4 ring-teal': form.mood_level === i + 1 }"
                  @click="form.mood_level = i + 1">{{ e }}</button>
        </div>
      </template>
      <template v-else>
        <h4 class="text-xl font-extrabold">Log a walk</h4>
        <div class="mt-3"><label class="label">Steps</label>
          <input v-model="form.steps" type="number" class="input mt-1" placeholder="e.g. 2000" /></div>
      </template>
      <div class="mt-4 flex gap-3">
        <button class="btn-primary flex-1" @click="submitQuick">Save</button>
        <button class="btn-ghost" @click="showQuick = false">Cancel</button>
      </div>
    </section>

    <section>
      <h3 class="text-xl font-extrabold">Health timeline</h3>
      <div v-if="loading" class="py-10 text-center text-ink/50">Loading…</div>
      <div v-else-if="timeline.length === 0" class="card text-center text-ink/60">No records yet.</div>
      <div v-for="(items, day) in byDay" :key="day" class="mt-4">
        <p class="label">{{ day }}</p>
        <div v-for="m in items" :key="m.id" class="card mt-2 flex items-center justify-between py-4">
          <div>
            <p class="font-extrabold">{{ labelFor(m.metric_type) }}</p>
            <p class="text-sm text-ink/60">{{ fmtTime(m.measured_at) }}</p>
          </div>
          <p class="text-xl font-extrabold">{{ valText(m) }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
