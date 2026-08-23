<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { api, fmtTime } from "@/services/api";
import { useI18n } from "@/i18n";

const { t } = useI18n();
const doses = ref<any[]>([]);
const medicines = ref<any[]>([]);
const loading = ref(true);
const showAdd = ref(false);
const newMed = ref({ name: "", dosage: "", frequency: "", scheduled_time: "08:00" });

const pending = computed(() => doses.value.filter((d) => d.status === "pending"));
const history = computed(() => doses.value.filter((d) => d.status !== "pending"));

onMounted(async () => {
  try {
    const [d, m] = await Promise.all([api("/medicines/today"), api("/medicines")]);
    doses.value = d;
    medicines.value = m;
  } finally {
    loading.value = false;
  }
});

const act = async (logId: number, action: "take" | "skip") => {
  const updated = await api(`/medicines/${action}/${logId}`, { method: "POST" });
  doses.value = doses.value.map((d) => (d.log_id === logId ? updated : d));
};

const addMedicine = async () => {
  if (!newMed.value.name) return;
  const med = await api("/medicines", { method: "POST", body: newMed.value });
  await api(`/medicines/${med.id}/schedules`, {
    method: "POST",
    body: { scheduled_time: newMed.value.scheduled_time, dosage_amount: newMed.value.dosage || null },
  });
  showAdd.value = false;
  newMed.value = { name: "", dosage: "", frequency: "", scheduled_time: "08:00" };
  medicines.value = await api("/medicines");
  doses.value = await api("/medicines/today");
};
</script>

<template>
  <div class="space-y-5">
    <section>
      <div class="flex items-center justify-between">
        <h3 class="text-xl font-extrabold">{{ t("meds.todayDoses") }}</h3>
        <button class="btn-ghost px-4 py-2" @click="showAdd = !showAdd">+ {{ t("meds.add") }}</button>
      </div>

      <div v-if="showAdd" class="card mt-3 space-y-3 bg-teal-light/50">
        <input v-model="newMed.name" class="input" :placeholder="t('meds.namePh')" />
        <div class="grid grid-cols-2 gap-3">
          <input v-model="newMed.dosage" class="input" :placeholder="t('meds.dosePh')" />
          <input v-model="newMed.scheduled_time" class="input" type="time" />
        </div>
        <input v-model="newMed.frequency" class="input" :placeholder="t('meds.freqPh')" />
        <button class="btn-primary w-full" @click="addMedicine">{{ t("meds.save") }}</button>
      </div>

      <div v-if="loading" class="py-10 text-center text-ink/50">{{ t("common.loading") }}</div>
      <div v-else-if="doses.length === 0" class="card text-center text-ink/60">{{ t("meds.noDoses") }}</div>

      <div v-for="d in doses" :key="d.log_id" class="card mt-3"
           :class="d.status === 'pending' ? 'border-l-8 border-teal' : 'opacity-70'">
        <div class="flex items-center gap-4">
          <span class="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-teal-light text-sm font-extrabold text-teal-dark">MED</span>
          <div class="flex-1">
            <p class="text-2xl font-extrabold">{{ d.medicine_name }}</p>
            <p class="text-ink/60">{{ d.scheduled_time }} · {{ d.dosage ? d.dosage + " " + d.dosage_unit : "" }}
              {{ d.instructions ? "· " + d.instructions : "" }}</p>
          </div>
          <span v-if="d.status === 'taken'" class="rounded-2xl bg-teal-light px-3 py-1.5 font-bold text-teal-dark">
            ✓ {{ fmtTime(d.taken_at) }}
          </span>
        </div>
        <div v-if="d.status === 'pending'" class="mt-3 flex gap-3">
          <button class="btn-primary flex-1" @click="act(d.log_id, 'take')">✓ {{ t("meds.tookIt") }}</button>
          <button class="btn-ghost" @click="act(d.log_id, 'skip')">{{ t("meds.skip") }}</button>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-xl font-extrabold">{{ t("meds.myMeds") }}</h3>
      <div v-for="m in medicines" :key="m.id" class="card mt-3">
        <p class="text-lg font-extrabold">{{ m.name }}</p>
        <p class="text-sm text-ink/60">{{ m.dosage ? m.dosage + " " + m.dosage_unit : "" }}
          {{ m.frequency ? "· " + m.frequency : "" }}</p>
      </div>
    </section>
  </div>
</template>
