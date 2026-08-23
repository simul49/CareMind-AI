<script setup lang="ts">
import { useI18n } from "@/i18n";

const { locale, setLocale } = useI18n();
</script>

<template>
  <div
    class="flex shrink-0 rounded-2xl bg-white/90 p-1 shadow-card"
    role="group"
    aria-label="Language"
  >
    <button
      class="rounded-xl px-3 py-1.5 text-sm font-extrabold transition"
      :class="locale === 'en' ? 'bg-teal text-white' : 'text-ink/50'"
      @click="setLocale('en')"
    >
      EN
    </button>
    <button
      class="rounded-xl px-3 py-1.5 text-sm font-extrabold transition"
      :class="locale === 'zh' ? 'bg-teal text-white' : 'text-ink/50'"
      @click="setLocale('zh')"
    >
      中文
    </button>
  </div>
</template>
