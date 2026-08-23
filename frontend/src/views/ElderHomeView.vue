<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { api, fmtTime } from "@/services/api";
import { useI18n } from "@/i18n";

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return t("greeting.morning");
  if (h < 18) return t("greeting.afternoon");
  return t("greeting.evening");
});

const moodLabels = ["mood.great", "mood.good", "mood.okay", "mood.low", "mood.poor"];

const firstName = computed(() => (auth.user?.full_name || "").split(" ")[0]);
const isElder = computed(() => auth.user?.role === "elder");

const today = ref<any>(null);
const doses = ref<any[]>([]);
const insights = ref<any[]>([]);
const overview = ref<any>(null);
const patients = ref<any[]>([]);
const mood = ref<number | null>(null);
const challenge = ref<any>(null);
const challengeBusy = ref(false);
const loading = ref(true);

const nextDose = computed(() => doses.value.find((d) => d.status === "pending") || doses.value[0] || null);

onMounted(async () => {
  try {
    if (auth.user?.role === "elder") {
      const [t, d, i, c] = await Promise.all([
        api("/health/today"),
        api("/medicines/today"),
        api("/ai/insights"),
        api("/challenges/today").catch(() => null),
      ]);
      today.value = t;
      doses.value = d;
      insights.value = i;
      challenge.value = c;
    } else if (auth.user?.role === "family" || auth.user?.role === "caregiver") {
      overview.value = await api("/caregiver/overview");
    } else if (auth.user?.role === "doctor") {
      patients.value = await api("/doctors/patients");
    }
  } catch (e: any) {
    console.error(e);
  } finally {
    loading.value = false;
  }
});

const takeDose = async (logId: number) => {
  const updated = await api(`/medicines/take/${logId}`, { method: "POST" });
  doses.value = doses.value.map((d) => (d.log_id === logId ? updated : d));
};

const logMood = async (level: number) => {
  mood.value = level;
  await api("/health/mood", { method: "POST", body: { mood_level: level } });
};

const completeChallenge = async () => {
  if (!challenge.value || challenge.value.done || challengeBusy.value) return;
  challengeBusy.value = true;
  try {
    challenge.value = await api("/challenges/today/complete", { method: "POST" });
  } finally {
    challengeBusy.value = false;
  }
};

// Localize seeded challenge cards (keyed by the stable badge slug from the backend)
const challengeLocal = computed(() => {
  const c = challenge.value;
  if (!c) return null;
  const key = String(c.badge || "").toLowerCase();
  const known = ["walk", "water", "stretch", "mood", "friends", "sleep", "mind"];
  if (!known.includes(key)) return c;
  return {
    ...c,
    badge: t(`challenge.${key}.badge`),
    category: t(`challenge.cat.${key}`),
    title: t(`challenge.${key}.title`),
    goal: t(`challenge.${key}.goal`),
  };
});
</script>

<template>
  <div class="space-y-5">
    <div v-if="loading" class="py-20 text-center text-ink/50 text-lg">{{ t("common.loading") }}</div>

    <!-- ELDER HOME -->
    <template v-else-if="isElder">
      <div class="rounded-3xl bg-gradient-to-br from-teal to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold text-teal-light">{{ greeting }}, {{ firstName }}</p>
        <h2 class="mt-1 text-3xl font-extrabold">{{ t("home.howFeel") }}</h2>
        <div class="mt-4 grid grid-cols-5 gap-2">
          <button v-for="(key, i) in moodLabels" :key="i"
                  class="rounded-2xl bg-white/15 px-2 py-3 text-sm font-extrabold transition hover:bg-white/30"
                  :class="{ 'ring-4 ring-white/70': mood === i + 1 }"
                  @click="logMood(i + 1)">
            {{ t(key) }}
          </button>
        </div>
        <p v-if="mood" class="mt-3 text-sm font-semibold text-teal-light">{{ t("mood.thanks") }}</p>
      </div>

      <!-- Today's Care -->
      <section>
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-extrabold">{{ t("home.todayCare") }}</h3>
          <button class="font-bold text-teal" @click="router.push('/app/medicines')">{{ t("home.allMeds") }} →</button>
        </div>
        <div v-if="nextDose" class="card mt-3 border-l-8 border-teal">
          <div class="flex items-start gap-4">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-teal-light text-sm font-extrabold text-teal-dark">MED</div>
            <div class="flex-1">
              <p class="text-sm font-bold text-ink/50">
                {{ nextDose.status === "pending" ? t("home.nextDose") : t("home.latestDose") }} · {{ nextDose.scheduled_time }}
              </p>
              <h4 class="text-2xl font-extrabold">{{ nextDose.medicine_name }}</h4>
              <p class="text-ink/60">{{ nextDose.dosage ? nextDose.dosage + " " + nextDose.dosage_unit : "" }}
                {{ nextDose.instructions ? "· " + nextDose.instructions : "" }}</p>
            </div>
          </div>
          <div class="mt-4 flex gap-3">
            <button v-if="nextDose.status === 'pending'" class="btn-primary flex-1" @click="takeDose(nextDose.log_id)">
              ✓ {{ t("home.tookIt") }}
            </button>
            <button v-else class="btn-ghost flex-1">{{ t("home.takenAt", { time: fmtTime(nextDose.taken_at) }) }} ✓</button>
            <button class="btn-ghost" @click="router.push('/app/medicines')">{{ t("home.allDoses") }}</button>
          </div>
        </div>
      </section>

      <!-- Today's wellness challenge -->
      <section v-if="challengeLocal">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-extrabold">{{ t("home.challenge") }}</h3>
          <span class="rounded-xl bg-teal-light px-3 py-1 text-xs font-extrabold text-teal-dark">
            {{ t("home.weekProgress", { done: challengeLocal.week_done }) }}
          </span>
        </div>
        <div class="card mt-3 bg-gradient-to-br from-teal-light/60 to-white">
          <div class="flex items-center gap-4">
            <span class="grid h-16 w-16 shrink-0 place-items-center rounded-3xl bg-white text-lg font-extrabold text-teal-dark shadow-card">
              {{ challengeLocal.badge }}
            </span>
            <div class="flex-1">
              <p class="text-[0.7rem] font-extrabold uppercase tracking-wide text-teal-dark">{{ challengeLocal.category }}</p>
              <h4 class="text-xl font-extrabold leading-snug">{{ challengeLocal.title }}</h4>
              <p class="mt-0.5 text-sm text-ink/60">{{ challengeLocal.goal }}</p>
            </div>
          </div>
          <div class="mt-4">
            <button
              v-if="!challengeLocal.done"
              class="btn-primary w-full"
              :disabled="challengeBusy"
              @click="completeChallenge"
            >
              {{ challengeBusy ? t("common.loading") : "✓ " + t("home.didIt") }}
            </button>
            <div v-else class="rounded-2xl bg-teal px-4 py-3 text-center font-extrabold text-white">
              {{ t("home.doneToday") }}
            </div>
          </div>
        </div>
      </section>

      <!-- Quick actions -->
      <section>
        <h3 class="text-xl font-extrabold">{{ t("home.familyReports") }}</h3>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <button class="card flex flex-col items-center gap-1.5 py-4 transition hover:-translate-y-0.5 hover:shadow-card" @click="router.push('/app/chat')">
            <span class="grid h-12 w-12 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">{{ t("nav.chat") }}</span>
            <span class="font-extrabold">{{ t("home.familyChat") }}</span>
            <span class="text-xs text-ink/50">{{ t("home.stayClose") }}</span>
          </button>
          <button class="card flex flex-col items-center gap-1.5 py-4 transition hover:-translate-y-0.5 hover:shadow-card" @click="router.push('/app/reports')">
            <span class="grid h-12 w-12 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">DOC</span>
            <span class="font-extrabold">{{ t("home.myReports") }}</span>
            <span class="text-xs text-ink/50">{{ t("home.aiExplains") }}</span>
          </button>
        </div>
      </section>

      <!-- Today's Health -->
      <section>
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-extrabold">{{ t("home.todayHealth") }}</h3>
          <button class="font-bold text-teal" @click="router.push('/app/health')">{{ t("home.fullTimeline") }} →</button>
        </div>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <div class="card">
            <p class="label">{{ t("home.bp") }}</p>
            <p class="mt-1 text-3xl font-extrabold">
              {{ today?.blood_pressure ? today.blood_pressure.systolic + "/" + today.blood_pressure.diastolic : "—" }}
            </p>
            <p class="text-sm font-semibold" :class="today?.blood_pressure?.systolic > 140 ? 'text-amber' : 'text-teal'">
              {{ today?.blood_pressure?.systolic > 140 ? t("home.slightlyHigh") : t("home.steady") }}
            </p>
          </div>
          <div class="card">
            <p class="label">{{ t("home.heartRate") }}</p>
            <p class="mt-1 text-3xl font-extrabold">{{ today?.heart_rate ? today.heart_rate.bpm + " bpm" : "—" }}</p>
          </div>
          <div class="card">
            <p class="label">{{ t("home.steps") }}</p>
            <p class="mt-1 text-3xl font-extrabold">{{ (today?.steps ?? 0).toLocaleString() }}</p>
            <p class="text-sm font-semibold text-teal">{{ t("home.target4000") }}</p>
          </div>
          <div class="card">
            <p class="label">{{ t("home.sleep") }}</p>
            <p class="mt-1 text-3xl font-extrabold">{{ today?.sleep_hours ? today.sleep_hours + " h" : "—" }}</p>
          </div>
        </div>
      </section>

      <!-- CareMind insight -->
      <section v-if="insights.length">
        <h3 class="text-xl font-extrabold">{{ t("home.fromCareMind") }}</h3>
        <div class="card mt-3 bg-gradient-to-br from-amber-light to-white">
          <div class="flex gap-3">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-amber-light text-lg font-extrabold text-amber">
              {{ insights[0].severity === "warning" ? "!" : "AI" }}
            </span>
            <div>
              <p class="font-extrabold">{{ insights[0].title }}</p>
              <p class="mt-1 text-ink/70">{{ insights[0].content }}</p>
              <button class="mt-3 font-bold text-teal" @click="router.push('/app/ai')">{{ t("home.askAbout") }} →</button>
            </div>
          </div>
        </div>
      </section>

      <section class="card bg-rose/5">
        <div class="flex items-center gap-4">
          <span class="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-rose/10 text-sm font-extrabold text-rose">SOS</span>
          <div class="flex-1">
            <p class="font-extrabold text-lg">{{ t("home.needHelp") }}</p>
            <p class="text-sm text-ink/60">{{ t("home.oneTap") }}</p>
          </div>
          <button class="btn-danger pulse-sos" @click="router.push('/app/emergency')">SOS</button>
        </div>
      </section>
    </template>

    <!-- FAMILY / CAREGIVER -->
    <template v-else-if="overview">
      <div class="rounded-3xl bg-gradient-to-br from-indigo-500 to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold">{{ t("family.welcome", { name: firstName }) }}</p>
        <h2 class="mt-1 text-3xl font-extrabold">{{ t("family.yourCare") }}</h2>
      </div>

      <div v-for="e in overview.elders" :key="e.id" class="card">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-extrabold">{{ e.name }} <span class="text-lg text-ink/50">({{ e.age }})</span></h3>
            <p class="text-sm text-ink/60">{{ e.city }}</p>
          </div>
          <div v-if="e.has_active_emergency" class="rounded-2xl bg-rose px-4 py-2 font-extrabold text-white">{{ t("emg.sosActive") }}</div>
        </div>

        <div class="mt-4 grid grid-cols-3 gap-3 text-center">
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">{{ (e.steps_today ?? 0).toLocaleString() }}</p>
            <p class="text-xs font-bold text-ink/60">{{ t("family.stepsToday") }}</p>
          </div>
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">{{ e.adherence_rate ?? "—" }}%</p>
            <p class="text-xs font-bold text-ink/60">{{ t("family.medication") }}</p>
          </div>
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">
              {{ e.latest_bp ? e.latest_bp.systolic + "/" + e.latest_bp.diastolic : "—" }}
            </p>
            <p class="text-xs font-bold text-ink/60">{{ t("family.latestBP") }}</p>
          </div>
        </div>

        <div v-if="e.last_post" class="mt-4 rounded-2xl bg-cream p-4">
          <p class="text-xs font-bold text-ink/50">{{ t("family.latestUpdate", { name: e.name.split(" ")[0] }) }}</p>
          <p class="mt-1">{{ e.last_post }}</p>
        </div>
      </div>
    </template>

    <!-- DOCTOR -->
    <template v-else-if="patients.length">
      <div class="rounded-3xl bg-gradient-to-br from-indigo-500 to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold">{{ t("doctor.welcome", { name: firstName }) }}</p>
        <h2 class="mt-1 text-3xl font-extrabold">{{ t("doctor.yourPatients") }}</h2>
      </div>
      <div v-for="p in patients" :key="p.patient_id" class="card">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-extrabold">{{ p.name }}</h3>
            <p class="text-sm text-ink/60">{{ t("doctor.years", { n: p.age }) }} · {{ p.city }}</p>
          </div>
          <span class="rounded-2xl bg-teal-light px-4 py-2 text-lg font-extrabold text-teal-dark">
            {{ p.latest_bp ? p.latest_bp.systolic + "/" + p.latest_bp.diastolic : "—" }}
          </span>
        </div>
        <div class="mt-3 flex items-center gap-3">
          <div class="h-3 flex-1 overflow-hidden rounded-full bg-ink/10">
            <div class="h-full rounded-full bg-teal" :style="{ width: (p.adherence_rate ?? 0) + '%' }"></div>
          </div>
          <span class="font-bold text-ink/60">{{ p.adherence_rate ?? "—" }}% {{ t("doc.adherenceLabel") }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
