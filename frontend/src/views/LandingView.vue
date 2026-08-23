<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "@/i18n";
import LangSwitcher from "@/components/LangSwitcher.vue";

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const quickLogin = async (email: string) => {
  try {
    await auth.login(email, "Password1!");
    router.push("/app/home");
  } catch (e: any) {
    alert(e.message);
  }
};

const features = [
  { badgeKey: "landing.f1Badge", titleKey: "landing.f1Title", descKey: "landing.f1Desc" },
  { badgeKey: "landing.f2Badge", titleKey: "landing.f2Title", descKey: "landing.f2Desc" },
  { badgeKey: "landing.f3Badge", titleKey: "landing.f3Title", descKey: "landing.f3Desc" },
  { badgeKey: "landing.f4Badge", titleKey: "landing.f4Title", descKey: "landing.f4Desc" },
  { badgeKey: "landing.f5Badge", titleKey: "landing.f5Title", descKey: "landing.f5Desc" },
  { badgeKey: "landing.f6Badge", titleKey: "landing.f6Title", descKey: "landing.f6Desc" },
];
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-teal-light via-cream to-amber-light/40">
    <div class="mx-auto max-w-5xl px-5 py-10 sm:py-16">
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="grid h-11 w-11 place-items-center rounded-2xl bg-teal text-sm font-extrabold text-white shadow-soft">CM</div>
          <span class="text-2xl font-extrabold tracking-tight">CareMind AI</span>
        </div>
        <div class="flex items-center gap-2">
          <LangSwitcher />
          <button class="btn-ghost" @click="router.push('/login')">{{ t("landing.signIn") }}</button>
        </div>
      </header>

      <section class="mt-14 text-center sm:mt-20">
        <h1 class="mx-auto max-w-3xl text-4xl font-extrabold leading-tight sm:text-6xl">
          {{ t("landing.hero1") }}
          <span class="text-teal">{{ t("landing.hero2") }}</span><br />
          {{ t("landing.hero3") }}
        </h1>
        <p class="mx-auto mt-6 max-w-2xl text-xl text-ink/70">
          {{ t("landing.heroDesc") }}
        </p>
        <div class="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button class="btn-primary px-8 py-4 text-xl" @click="router.push('/register')">
            {{ t("landing.ctaFree") }}
          </button>
          <button class="btn-ghost px-8 py-4 text-xl" @click="router.push('/login')">
            {{ t("landing.ctaExisting") }}
          </button>
        </div>

        <div class="mt-10 rounded-3xl bg-white/70 p-4 shadow-soft backdrop-blur">
          <p class="label mb-3">{{ t("landing.demoTitle") }}</p>
          <div class="flex flex-wrap justify-center gap-3">
            <button class="btn bg-teal-light px-5 py-2.5 text-teal-dark" @click="quickLogin('rahma@caremind.demo')">
              {{ t("landing.demoElder") }}
            </button>
            <button class="btn bg-rose/10 px-5 py-2.5 text-rose" @click="quickLogin('nadia@caremind.demo')">
              {{ t("landing.demoDaughter") }}
            </button>
            <button class="btn bg-indigo-100 px-5 py-2.5 text-indigo-700" @click="quickLogin('doctor@caremind.demo')">
              {{ t("landing.demoDoctor") }}
            </button>
          </div>
        </div>
      </section>

      <section class="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="f in features" :key="f.titleKey" class="card transition hover:-translate-y-1 hover:shadow-glow">
          <div class="grid h-14 w-14 place-items-center rounded-2xl bg-teal-light text-sm font-extrabold text-teal-dark">{{ t(f.badgeKey) }}</div>
          <h3 class="mt-3 text-xl font-extrabold">{{ t(f.titleKey) }}</h3>
          <p class="mt-1 text-ink/70">{{ t(f.descKey) }}</p>
        </div>
      </section>

      <footer class="mt-16 pb-6 text-center text-sm text-ink/50">
        {{ t("landing.footer") }}
      </footer>
    </div>
  </div>
</template>
