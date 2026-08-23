<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { api, fmtTime } from "@/services/api";

const router = useRouter();
const auth = useAuthStore();

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
});

const firstName = computed(() => (auth.user?.full_name || "").split(" ")[0]);
const isElder = computed(() => auth.user?.role === "elder");

const today = ref<any>(null);
const doses = ref<any[]>([]);
const insights = ref<any[]>([]);
const overview = ref<any>(null);
const patients = ref<any[]>([]);
const mood = ref<number | null>(null);
const loading = ref(true);

const nextDose = computed(() => doses.value.find((d) => d.status === "pending") || doses.value[0] || null);

onMounted(async () => {
  try {
    if (auth.user?.role === "elder") {
      const [t, d, i] = await Promise.all([
        api("/health/today"),
        api("/medicines/today"),
        api("/ai/insights"),
      ]);
      today.value = t;
      doses.value = d;
      insights.value = i;
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
</script>

<template>
  <div class="space-y-5">
    <div v-if="loading" class="py-20 text-center text-ink/50 text-lg">Loading…</div>

    <!-- ELDER HOME -->
    <template v-else-if="isElder">
      <div class="rounded-3xl bg-gradient-to-br from-teal to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold text-teal-light">{{ greeting }}, {{ firstName }} 👋</p>
        <h2 class="mt-1 text-3xl font-extrabold">How are you feeling today?</h2>
        <div class="mt-4 flex gap-3">
          <button v-for="(e, i) in ['😊', '🙂', '😐', '😔', '😟']" :key="i"
                  class="grid h-14 w-14 place-items-center rounded-2xl bg-white/15 text-3xl transition hover:bg-white/30"
                  :class="{ 'ring-4 ring-white/70': mood === i + 1 }"
                  @click="logMood(i + 1)">
            {{ e }}
          </button>
        </div>
        <p v-if="mood" class="mt-3 text-sm font-semibold text-teal-light">Thanks — I've noted that for your care circle. 💙</p>
      </div>

      <!-- Today's Care -->
      <section>
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-extrabold">Today's Care</h3>
          <button class="font-bold text-teal" @click="router.push('/app/medicines')">All medicines →</button>
        </div>
        <div v-if="nextDose" class="card mt-3 border-l-8 border-teal">
          <div class="flex items-start gap-4">
            <div class="text-5xl">💊</div>
            <div class="flex-1">
              <p class="text-sm font-bold text-ink/50">
                {{ nextDose.status === "pending" ? "Next dose" : "Latest dose" }} · {{ nextDose.scheduled_time }}
              </p>
              <h4 class="text-2xl font-extrabold">{{ nextDose.medicine_name }}</h4>
              <p class="text-ink/60">{{ nextDose.dosage ? nextDose.dosage + " " + nextDose.dosage_unit : "" }}
                {{ nextDose.instructions ? "· " + nextDose.instructions : "" }}</p>
            </div>
          </div>
          <div class="mt-4 flex gap-3">
            <button v-if="nextDose.status === 'pending'" class="btn-primary flex-1" @click="takeDose(nextDose.log_id)">
              ✓ I took it
            </button>
            <button v-else class="btn-ghost flex-1">Taken {{ fmtTime(nextDose.taken_at) }} ✓</button>
            <button class="btn-ghost" @click="router.push('/app/medicines')">All doses</button>
          </div>
        </div>
      </section>

      <!-- Quick actions -->
      <section>
        <h3 class="text-xl font-extrabold">Family & reports</h3>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <button class="card flex flex-col items-center gap-1.5 py-4 transition hover:-translate-y-0.5 hover:shadow-card" @click="router.push('/app/chat')">
            <span class="text-3xl">💬</span>
            <span class="font-extrabold">Family chat</span>
            <span class="text-xs text-ink/50">Stay close</span>
          </button>
          <button class="card flex flex-col items-center gap-1.5 py-4 transition hover:-translate-y-0.5 hover:shadow-card" @click="router.push('/app/reports')">
            <span class="text-3xl">📄</span>
            <span class="font-extrabold">My reports</span>
            <span class="text-xs text-ink/50">AI explains them</span>
          </button>
        </div>
      </section>

      <!-- Today's Health -->
      <section>
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-extrabold">Today's Health</h3>
          <button class="font-bold text-teal" @click="router.push('/app/health')">Full timeline →</button>
        </div>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <div class="card">
            <p class="label">Blood pressure</p>
            <p class="mt-1 text-3xl font-extrabold">
              {{ today?.blood_pressure ? today.blood_pressure.systolic + "/" + today.blood_pressure.diastolic : "—" }}
            </p>
            <p class="text-sm font-semibold" :class="today?.blood_pressure?.systolic > 140 ? 'text-amber' : 'text-teal'">
              {{ today?.blood_pressure?.systolic > 140 ? "Slightly high" : "Steady" }}
            </p>
          </div>
          <div class="card">
            <p class="label">Heart rate</p>
            <p class="mt-1 text-3xl font-extrabold">{{ today?.heart_rate ? today.heart_rate.bpm + " bpm" : "—" }}</p>
          </div>
          <div class="card">
            <p class="label">Steps</p>
            <p class="mt-1 text-3xl font-extrabold">{{ (today?.steps ?? 0).toLocaleString() }}</p>
            <p class="text-sm font-semibold text-teal">Target 4,000</p>
          </div>
          <div class="card">
            <p class="label">Sleep</p>
            <p class="mt-1 text-3xl font-extrabold">{{ today?.sleep_hours ? today.sleep_hours + " h" : "—" }}</p>
          </div>
        </div>
      </section>

      <!-- CareMind insight -->
      <section v-if="insights.length">
        <h3 class="text-xl font-extrabold">From CareMind AI</h3>
        <div class="card mt-3 bg-gradient-to-br from-amber-light to-white">
          <div class="flex gap-3">
            <span class="text-3xl">{{ insights[0].severity === "warning" ? "🔎" : "💡" }}</span>
            <div>
              <p class="font-extrabold">{{ insights[0].title }}</p>
              <p class="mt-1 text-ink/70">{{ insights[0].content }}</p>
              <button class="mt-3 font-bold text-teal" @click="router.push('/app/ai')">Ask CareMind about it →</button>
            </div>
          </div>
        </div>
      </section>

      <section class="card bg-rose/5">
        <div class="flex items-center gap-4">
          <span class="text-4xl">🛟</span>
          <div class="flex-1">
            <p class="font-extrabold text-lg">Need help right now?</p>
            <p class="text-sm text-ink/60">One tap alerts your family and finds the nearest hospital.</p>
          </div>
          <button class="btn-danger pulse-sos" @click="router.push('/app/emergency')">SOS</button>
        </div>
      </section>
    </template>

    <!-- FAMILY / CAREGIVER -->
    <template v-else-if="overview">
      <div class="rounded-3xl bg-gradient-to-br from-indigo-500 to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold">Welcome, {{ firstName }}</p>
        <h2 class="mt-1 text-3xl font-extrabold">Your family's care</h2>
      </div>

      <div v-for="e in overview.elders" :key="e.id" class="card">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-extrabold">{{ e.name }} <span class="text-lg text-ink/50">({{ e.age }})</span></h3>
            <p class="text-sm text-ink/60">{{ e.city }}</p>
          </div>
          <div v-if="e.has_active_emergency" class="rounded-2xl bg-rose px-4 py-2 font-extrabold text-white">🚨 SOS ACTIVE</div>
        </div>

        <div class="mt-4 grid grid-cols-3 gap-3 text-center">
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">{{ (e.steps_today ?? 0).toLocaleString() }}</p>
            <p class="text-xs font-bold text-ink/60">Steps today</p>
          </div>
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">{{ e.adherence_rate ?? "—" }}%</p>
            <p class="text-xs font-bold text-ink/60">Medication</p>
          </div>
          <div class="rounded-2xl bg-teal-light p-3">
            <p class="text-2xl font-extrabold text-teal-dark">
              {{ e.latest_bp ? e.latest_bp.systolic + "/" + e.latest_bp.diastolic : "—" }}
            </p>
            <p class="text-xs font-bold text-ink/60">Latest BP</p>
          </div>
        </div>

        <div v-if="e.last_post" class="mt-4 rounded-2xl bg-cream p-4">
          <p class="text-xs font-bold text-ink/50">Latest update from {{ e.name.split(" ")[0] }}</p>
          <p class="mt-1">{{ e.last_post }}</p>
        </div>
      </div>
    </template>

    <!-- DOCTOR -->
    <template v-else-if="patients.length">
      <div class="rounded-3xl bg-gradient-to-br from-indigo-500 to-teal-dark p-6 text-white shadow-soft">
        <p class="text-lg font-semibold">Welcome, {{ firstName }}</p>
        <h2 class="mt-1 text-3xl font-extrabold">Your patients</h2>
      </div>
      <div v-for="p in patients" :key="p.patient_id" class="card">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-extrabold">{{ p.name }}</h3>
            <p class="text-sm text-ink/60">{{ p.age }} yrs · {{ p.city }}</p>
          </div>
          <span class="rounded-2xl bg-teal-light px-4 py-2 text-lg font-extrabold text-teal-dark">
            {{ p.latest_bp ? p.latest_bp.systolic + "/" + p.latest_bp.diastolic : "—" }}
          </span>
        </div>
        <div class="mt-3 flex items-center gap-3">
          <div class="h-3 flex-1 overflow-hidden rounded-full bg-ink/10">
            <div class="h-full rounded-full bg-teal" :style="{ width: (p.adherence_rate ?? 0) + '%' }"></div>
          </div>
          <span class="font-bold text-ink/60">{{ p.adherence_rate ?? "—" }}% adherence</span>
        </div>
      </div>
    </template>
  </div>
</template>
