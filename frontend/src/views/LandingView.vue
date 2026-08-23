<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const quickLogin = async (email: string) => {
  try {
    await auth.login(email, "Password1!");
    router.push("/app/home");
  } catch (e: any) {
    alert(e.message);
  }
};

const features = [
  { emoji: "💊", title: "Medicine Reminders", desc: "Never miss a dose. One-tap confirm, gentle reminders." },
  { emoji: "❤️", title: "Health Timeline", desc: "BP, heart rate, sleep & activity — all in one simple timeline." },
  { emoji: "🤖", title: "CareMind AI", desc: "A kind companion that understands your health context." },
  { emoji: "🛟", title: "SOS Emergency", desc: "One big button. Family alerted, nearby hospital found." },
  { emoji: "👨‍👩‍👧", title: "Family Circle", desc: "Moments, chat and peace of mind for the whole family." },
  { emoji: "🧑‍⚕️", title: "Doctor Connect", desc: "Your doctor sees the real picture — with your consent." },
];
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-teal-light via-cream to-amber-light/40">
    <div class="mx-auto max-w-5xl px-5 py-10 sm:py-16">
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="grid h-11 w-11 place-items-center rounded-2xl bg-teal text-2xl text-white shadow-soft">💙</div>
          <span class="text-2xl font-extrabold tracking-tight">CareMind AI</span>
        </div>
        <button class="btn-ghost" @click="router.push('/login')">Sign in</button>
      </header>

      <section class="mt-14 text-center sm:mt-20">
        <h1 class="mx-auto max-w-3xl text-4xl font-extrabold leading-tight sm:text-6xl">
          Smart Care.
          <span class="text-teal">Safe Living.</span><br />
          Peace of Mind.
        </h1>
        <p class="mx-auto mt-6 max-w-2xl text-xl text-ink/70">
          A private AI-powered care ecosystem that connects older adults, their family,
          their trusted doctor — and a caring AI companion.
        </p>
        <div class="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button class="btn-primary px-8 py-4 text-xl" @click="router.push('/register')">
            Get started — it's free
          </button>
          <button class="btn-ghost px-8 py-4 text-xl" @click="router.push('/login')">
            I already have an account
          </button>
        </div>

        <div class="mt-10 rounded-3xl bg-white/70 p-4 shadow-soft backdrop-blur">
          <p class="label mb-3">🎯 Hackathon demo — try a seeded account</p>
          <div class="flex flex-wrap justify-center gap-3">
            <button class="btn bg-teal-light px-5 py-2.5 text-teal-dark" @click="quickLogin('rahma@caremind.demo')">
              👵 Rahima (Elder)
            </button>
            <button class="btn bg-rose/10 px-5 py-2.5 text-rose" @click="quickLogin('nadia@caremind.demo')">
              👩 Nadia (Daughter)
            </button>
            <button class="btn bg-indigo-100 px-5 py-2.5 text-indigo-700" @click="quickLogin('doctor@caremind.demo')">
              🧑‍⚕️ Dr. Rahman (Doctor)
            </button>
          </div>
        </div>
      </section>

      <section class="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="f in features" :key="f.title" class="card transition hover:-translate-y-1 hover:shadow-glow">
          <div class="text-4xl">{{ f.emoji }}</div>
          <h3 class="mt-3 text-xl font-extrabold">{{ f.title }}</h3>
          <p class="mt-1 text-ink/70">{{ f.desc }}</p>
        </div>
      </section>

      <footer class="mt-16 pb-6 text-center text-sm text-ink/50">
        CareMind AI — built for the 3-day hackathon. The AI companions, it never replaces a doctor. 💙
      </footer>
    </div>
  </div>
</template>
