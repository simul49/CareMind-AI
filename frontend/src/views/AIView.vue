<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { api } from "@/services/api";
import { useI18n } from "@/i18n";

const { t, isZh } = useI18n();
const messages = ref<any[]>([]);
const input = ref("");
const conversationId = ref<number | null>(null);
const loading = ref(false);
const chatsEl = ref<HTMLElement | null>(null);
const starterVisible = ref(true);

// ---- Voice ----
const listening = ref(false);
const speakOn = ref(false);
const voiceSupported =
  typeof window !== "undefined" && !!(window as any).SpeechRecognition || !!(window as any).webkitSpeechRecognition;
const ttsSupported = typeof window !== "undefined" && "speechSynthesis" in window;
let recognition: any = null;

const chips = ["ai.chip1", "ai.chip2", "ai.chip3", "ai.chip4"];

onMounted(async () => {
  try {
    const convs = await api("/ai/conversations");
    if (convs.length) {
      conversationId.value = convs[0].id;
      messages.value = await api(`/ai/conversations/${convs[0].id}/messages`);
      starterVisible.value = messages.value.length === 0;
      scrollDown();
    }
  } catch (e) {
    console.error(e);
  }
  // Prefilled question (e.g. from a report detail → "Explain it to me")
  const prefill = sessionStorage.getItem("caremind_question");
  if (prefill) {
    sessionStorage.removeItem("caremind_question");
    setTimeout(() => send(prefill), 700);
  }
});

const scrollDown = async () => {
  await nextTick();
  chatsEl.value?.scrollTo({ top: chatsEl.value.scrollHeight, behavior: "smooth" });
};

function speak(text: string) {
  if (!ttsSupported || !speakOn.value) return;
  try {
    window.speechSynthesis.cancel();
    const clean = text.replace(/\p{Extended_Pictographic}/gu, "");
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = isZh.value ? "zh-CN" : "en-US";
    u.rate = 0.95;
    u.pitch = 1.05;
    window.speechSynthesis.speak(u);
  } catch (e) {
    /* voice is a bonus */
  }
}

function toggleMic() {
  if (listening.value) {
    recognition?.stop();
    return;
  }
  if (!voiceSupported) return;
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  recognition = recognition || new SR();
  recognition.lang = isZh.value ? "zh-CN" : "en-US";
  recognition.interimResults = false;
  recognition.onresult = (e: any) => {
    const t = e.results[0][0].transcript;
    input.value = t;
    listenAndSpeak();
    send(t);
  };
  recognition.onerror = () => (listening.value = false);
  recognition.onend = () => (listening.value = false);
  listening.value = true;
  recognition.start();
}

const listenAndSpeak = () => {
  if (!speakOn.value) speakOn.value = true;
};

const send = async (text?: string) => {
  const content = (text ?? input.value).trim();
  if (!content || loading.value) return;
  input.value = "";
  starterVisible.value = false;
  messages.value.push({ id: Date.now(), sender: "user", content, created_at: new Date().toISOString() });
  loading.value = true;
  scrollDown();
  try {
    const res = await api("/ai/chat", {
      method: "POST",
      body: { conversation_id: conversationId.value, message: content, lang: isZh.value ? "zh" : "en" },
    });
    conversationId.value = res.conversation_id;
    messages.value.push({
      id: Date.now() + 1,
      sender: "assistant",
      content: res.reply,
      created_at: new Date().toISOString(),
    });
    speak(res.reply);
  } catch (e: any) {
    messages.value.push({ id: Date.now() + 2, sender: "assistant", content: t("ai.error"), created_at: new Date().toISOString() });
  } finally {
    loading.value = false;
    scrollDown();
  }
};
</script>

<template>
  <div class="flex h-[calc(100vh-180px)] flex-col">
    <div ref="chatsEl" class="flex-1 space-y-3 overflow-y-auto pb-3 pr-1">
      <div v-if="starterVisible" class="rounded-3xl bg-teal p-5 text-white shadow-soft">
        <span class="grid h-14 w-14 place-items-center rounded-2xl bg-white/15 text-xl font-extrabold">AI</span>
        <h3 class="mt-1 text-xl font-extrabold">{{ t("ai.hi") }}</h3>
        <p class="mt-1 text-teal-light">
          {{ t("ai.intro") }}
        </p>
        <button
          v-if="ttsSupported"
          class="mt-3 rounded-2xl bg-white/15 px-4 py-2 text-sm font-extrabold"
          :class="{ 'bg-white text-teal-dark': speakOn }"
          @click="speakOn = !speakOn"
        >
          {{ speakOn ? t("ai.speakOn") : t("ai.speakOff") }}
        </button>
      </div>

      <div v-for="m in messages" :key="m.id"
           :class="m.sender === 'user' ? 'ml-auto max-w-[80%] rounded-3xl bg-teal px-4 py-3 text-white' : 'mr-auto max-w-[85%] rounded-3xl bg-white px-4 py-3 shadow-card'">
        <p class="whitespace-pre-wrap text-[1.05rem] leading-relaxed">{{ m.content }}</p>
      </div>

      <div v-if="loading" class="mr-auto max-w-[85%] rounded-3xl bg-white px-4 py-3 shadow-card">
        <span class="text-ink/50">{{ t("ai.typing") }}<span class="animate-pulse">…</span></span>
      </div>
    </div>

    <div v-if="starterVisible" class="mb-2 flex flex-wrap gap-2">
      <button v-for="c in chips" :key="c" class="rounded-2xl bg-teal-light px-4 py-2 text-left text-sm font-bold text-teal-dark transition hover:bg-teal/20"
              @click="send(t(c))">{{ t(c) }}</button>
    </div>

    <form class="flex gap-2" @submit.prevent="send()">
      <button
        v-if="voiceSupported"
        type="button"
        class="grid h-12 shrink-0 place-items-center rounded-2xl px-4 text-sm font-extrabold transition"
        :class="listening ? 'animate-pulse bg-rose text-white' : 'bg-white text-ink shadow-card'"
        :title="listening ? t('ai.listening') : t('ai.speakTo')"
        @click="toggleMic"
      >
        {{ t("ai.talk") }}
      </button>
      <input v-model="input" class="input flex-1" :placeholder="t('ai.placeholder')" />
      <button type="submit" class="btn-primary px-6" :disabled="loading">{{ t("ai.send") }}</button>
    </form>
    <p v-if="listening" class="mt-1 text-center text-xs font-bold text-rose animate-pulse">
      {{ t("ai.listeningHint") }}
    </p>
  </div>
</template>
