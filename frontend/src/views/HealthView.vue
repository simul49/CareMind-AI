<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api, fmtDay, fmtTime } from "@/services/api";
import { useI18n } from "@/i18n";

const { t } = useI18n();
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

const labelFor = (type: string) =>
  ({
    blood_pressure: t("health.bp"),
    heart_rate: t("health.heartRate"),
    sleep: t("health.sleep"),
    activity: t("health.activity"),
    mood: t("health.mood"),
    weight: t("health.weight"),
  }[type] || type);

const valText = (m: any) => {
  const v = m.values;
  if (m.metric_type === "blood_pressure") return `${v.systolic}/${v.diastolic} mmHg`;
  if (m.metric_type === "heart_rate") return `${v.bpm} bpm`;
  if (m.metric_type === "sleep") return `${v.sleep_hours} h`;
  if (m.metric_type === "activity") return `${v.steps?.toLocaleString() ?? ""} ${t("health.stepsUnit")}`;
  if (m.metric_type === "mood") return t(["mood.poor", "mood.low", "mood.okay", "mood.good", "mood.great"][v.mood_level - 1] || "mood.okay");
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
      <h3 class="text-xl font-extrabold">{{ t("health.quickLog") }}</h3>
      <div class="mt-3 grid grid-cols-3 gap-3">
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('bp')">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">BP</span><p class="mt-1 font-extrabold">{{ t("health.bp") }}</p>
        </button>
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('mood')">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">{{ t("health.mood").slice(0, 4) }}</span><p class="mt-1 font-extrabold">{{ t("health.feeling") }}</p>
        </button>
        <button class="card text-center transition hover:-translate-y-0.5" @click="openQuick('walk')">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">{{ t("health.walk") }}</span><p class="mt-1 font-extrabold">{{ t("health.walk") }}</p>
        </button>
      </div>
    </section>

    <section v-if="showQuick" class="card bg-teal-light/50">
      <template v-if="quickType === 'bp'">
        <h4 class="text-xl font-extrabold">{{ t("health.logBp") }}</h4>
        <div class="mt-3 grid grid-cols-3 gap-3">
          <div><label class="label">{{ t("health.systolic") }}</label><input v-model="form.systolic" type="number" class="input mt-1" placeholder="138" /></div>
          <div><label class="label">{{ t("health.diastolic") }}</label><input v-model="form.diastolic" type="number" class="input mt-1" placeholder="86" /></div>
          <div><label class="label">{{ t("health.pulse") }}</label><input v-model="form.bpm" type="number" class="input mt-1" placeholder="74" /></div>
        </div>
      </template>
      <template v-else-if="quickType === 'mood'">
        <h4 class="text-xl font-extrabold">{{ t("health.howFeel") }}</h4>
        <div class="mt-3 grid grid-cols-5 gap-2">
          <button v-for="(key, i) in ['mood.poor', 'mood.low', 'mood.okay', 'mood.good', 'mood.great']" :key="i"
                  class="rounded-2xl bg-white px-2 py-3 text-sm font-extrabold"
                  :class="{ 'ring-4 ring-teal': form.mood_level === i + 1 }"
                  @click="form.mood_level = i + 1">{{ t(key) }}</button>
        </div>
      </template>
      <template v-else>
        <h4 class="text-xl font-extrabold">{{ t("health.logWalk") }}</h4>
        <div class="mt-3"><label class="label">{{ t("health.steps") }}</label>
          <input v-model="form.steps" type="number" class="input mt-1" :placeholder="t('health.walkPh')" /></div>
      </template>
      <div class="mt-4 flex gap-3">
        <button class="btn-primary flex-1" @click="submitQuick">{{ t("common.save") }}</button>
        <button class="btn-ghost" @click="showQuick = false">{{ t("common.cancel") }}</button>
      </div>
    </section>

    <section>
      <h3 class="text-xl font-extrabold">{{ t("health.timeline") }}</h3>
      <div v-if="loading" class="py-10 text-center text-ink/50">{{ t("common.loading") }}</div>
      <div v-else-if="timeline.length === 0" class="card text-center text-ink/60">{{ t("health.noRecords") }}</div>
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
