<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/services/api";

const contacts = ref<any[]>([]);
const events = ref<any[]>([]);
const active = ref<any>(null);
const triggered = ref<any>(null);
const confirming = ref(false);

onMounted(async () => {
  try {
    const [c, e] = await Promise.all([api("/emergency/contacts"), api("/emergency/events")]);
    contacts.value = c;
    events.value = e;
    active.value = e.find((ev: any) => ev.status === "active") || null;
  } catch (err) {
    console.error(err);
  }
});

const triggerSos = async () => {
  confirming.value = true;
  try {
    triggered.value = await api("/emergency/trigger", { method: "POST", body: { trigger_type: "manual" } });
    const events = await api("/emergency/events");
    active.value = events.find((ev: any) => ev.status === "active") || null;
  } finally {
    confirming.value = false;
  }
};

const resolve = async () => {
  if (!active.value) return;
  await api(`/emergency/events/${active.value.id}/resolve`, { method: "POST", body: { summary: "I'm okay now." } });
  active.value = null;
  events.value = await api("/emergency/events");
};
</script>

<template>
  <div class="space-y-5">
    <!-- ACTIVE SOS -->
    <div v-if="active" class="card bg-gradient-to-br from-rose to-rose/80 text-center text-white">
      <span class="mx-auto inline-block rounded-2xl bg-white/15 px-5 py-2 text-xl font-extrabold tracking-widest">SOS ACTIVE</span>
      <h3 class="mt-3 text-3xl font-extrabold">Help is on the way</h3>
      <p class="mt-1 text-white/85">Your emergency alert is active.</p>
      <div class="mx-auto mt-5 max-w-xs space-y-2 rounded-2xl bg-white/15 p-4 text-left">
        <p>Location: {{ active.location_label || "Home" }}</p>
        <p>Hospital: City General Hospital — 5 min away</p>
        <p>Notified: {{ contacts.length }} contact(s)</p>
      </div>
      <button class="btn mt-6 w-full bg-white text-rose py-4 text-xl font-extrabold" @click="resolve">
        ✓ I'm okay now — stop alert
      </button>
    </div>

    <!-- TRIGGER SCREEN -->
    <div v-else-if="triggered" class="card text-center">
      <span class="mx-auto inline-block rounded-2xl bg-teal px-5 py-2 text-lg font-extrabold tracking-widest text-white">SOS SENT</span>
      <h3 class="mt-3 text-2xl font-extrabold text-teal-dark">Emergency alert sent</h3>
      <div class="mx-auto mt-4 max-w-sm space-y-2 rounded-2xl bg-teal-light/50 p-4 text-left">
        <p>Hospital: {{ triggered.hospital.name }} — {{ triggered.hospital.distance_km }} km away</p>
        <p v-for="c in triggered.contacts_notified" :key="c.phone">SMS sent to {{ c.name }} ({{ c.phone }})</p>
      </div>
      <button class="btn-ghost mt-4" @click="triggered = null">Back</button>
    </div>

    <!-- IDLE SOS -->
    <div v-else class="text-center">
      <button class="pulse-sos mx-auto grid h-56 w-56 place-items-center rounded-full bg-rose text-white shadow-soft transition active:scale-95"
              @click="triggerSos">
        <div>
          <p class="text-5xl font-extrabold tracking-wide">SOS</p>
          <p class="mt-1 text-sm font-semibold text-white/85">Tap for help</p>
        </div>
      </button>
      <p class="mx-auto mt-5 max-w-xs text-ink/60">
        This alerts your family and finds the nearest hospital. Only use in a real emergency.
      </p>
    </div>

    <!-- Contacts -->
    <section>
      <h3 class="text-xl font-extrabold">Emergency contacts</h3>
      <div v-for="c in contacts" :key="c.id" class="card mt-3 flex items-center gap-4">
        <div class="grid h-12 w-12 place-items-center rounded-full text-xs font-extrabold"
             :class="c.is_primary ? 'bg-rose/10 text-rose' : 'bg-teal-light text-teal-dark'">{{ c.is_primary ? "Main" : "Call" }}</div>
        <div class="flex-1">
          <p class="font-extrabold">{{ c.name }} <span v-if="c.is_primary" class="text-xs text-rose">primary</span></p>
          <p class="text-sm text-ink/60">{{ c.relationship_type }} · {{ c.phone }}</p>
        </div>
      </div>
    </section>

    <!-- History -->
    <section v-if="events.length">
      <h3 class="text-xl font-extrabold">Past alerts</h3>
      <div v-for="e in events" :key="e.id" class="card mt-3">
        <p class="font-extrabold" :class="e.status === 'resolved' ? 'text-teal' : 'text-rose'">
          {{ e.status === "resolved" ? "Resolved" : e.status.toUpperCase() }}
        </p>
        <p class="text-sm text-ink/60">{{ new Date(e.started_at).toLocaleString() }}</p>
      </div>
    </section>
  </div>
</template>
