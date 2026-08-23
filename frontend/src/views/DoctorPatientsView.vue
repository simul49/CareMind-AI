<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "@/services/api";
import { useI18n } from "@/i18n";

const router = useRouter();
const { t } = useI18n();
const patients = ref<any[]>([]);
const loading = ref(true);
const error = ref("");

const avg = () => {
  const vals = patients.value.map((p) => p.adherence_rate).filter((x) => x != null);
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null;
};

onMounted(async () => {
  try {
    patients.value = await api("/doctors/patients");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="text-2xl font-extrabold">{{ t("doc.title") }}</h2>
      <p class="text-sm text-ink/60">{{ t("doc.sub") }}</p>
    </div>

    <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>
    <div v-if="loading" class="py-16 text-center text-ink/50">{{ t("common.loading") }}</div>

    <!-- Stats -->
    <div v-if="patients.length" class="grid grid-cols-2 gap-3">
      <div class="card">
        <p class="text-3xl font-extrabold text-teal-dark">{{ patients.length }}</p>
        <p class="text-xs font-bold text-ink/50">{{ t("doc.patients") }}</p>
      </div>
      <div class="card">
        <p class="text-3xl font-extrabold text-teal-dark">{{ avg() ?? "—" }}%</p>
        <p class="text-xs font-bold text-ink/50">{{ t("doc.adherence") }}</p>
      </div>
    </div>

    <!-- Patient cards -->
    <button
      v-for="p in patients"
      :key="p.patient_id"
      class="card flex w-full items-center gap-4 text-left transition hover:-translate-y-0.5 hover:shadow-card"
      @click="router.push(`/app/doctor/patient/${p.patient_id}`)"
    >
      <span class="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-teal text-2xl text-white">
        {{ p.name?.charAt(0) }}
      </span>
      <div class="min-w-0 flex-1">
        <p class="truncate font-extrabold text-lg">{{ p.name }}</p>
        <p class="text-sm text-ink/60">{{ p.age ?? "—" }} {{ t("doc.years") }} · {{ p.city || "—" }}</p>
        <p v-if="p.latest_bp" class="mt-1 text-sm font-extrabold text-teal-dark">
          {{ t("doc.bp") }} {{ p.latest_bp.systolic }}/{{ p.latest_bp.diastolic }}
        </p>
        <p v-else class="mt-1 text-sm text-ink/40">{{ t("doc.noBp") }}</p>
      </div>
      <div class="text-right">
        <div class="relative mx-auto h-14 w-14">
          <svg viewBox="0 0 36 36" class="h-14 w-14 -rotate-90">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e8e9e0" stroke-width="3.4" />
            <circle
              cx="18" cy="18" r="15.9" fill="none"
              :stroke="(p.adherence_rate ?? 0) >= 80 ? '#2d8f88' : (p.adherence_rate ?? 0) >= 50 ? '#d9a441' : '#c75d68'"
              stroke-width="3.4" stroke-linecap="round"
              :stroke-dasharray="`${(p.adherence_rate ?? 0) * 1.0} 100`"
            />
          </svg>
          <span class="absolute inset-0 grid place-items-center text-xs font-extrabold">{{ p.adherence_rate ?? "—" }}%</span>
        </div>
        <p class="mt-1 text-[0.65rem] font-bold text-ink/40">{{ t("doc.adherenceLabel") }}</p>
      </div>
    </button>

    <div v-if="!loading && !patients.length" class="card py-10 text-center">
      <p class="mt-2 font-extrabold">{{ t("doc.empty") }}</p>
      <p class="text-sm text-ink/60">{{ t("doc.emptySub") }}</p>
    </div>
  </div>
</template>
