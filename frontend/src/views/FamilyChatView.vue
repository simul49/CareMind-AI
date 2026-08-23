<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { api, fmtTime } from "@/services/api";

const auth = useAuthStore();
const conversations = ref<any[]>([]);
const messages = ref<any[]>([]);
const activeId = ref<number | null>(null);
const activeTitle = ref("");
const input = ref("");
const loading = ref(false);
const error = ref("");
const chatsEl = ref<HTMLElement | null>(null);
let pollTimer: ReturnType<typeof setInterval> | null = null;

const chips = [
  "Did you take your medicine?",
  "How are you feeling today?",
  "A short walk helps the heart!",
  "Call me when you're free",
];

onMounted(async () => {
  try {
    conversations.value = await api("/care/conversations");
    if (conversations.value.length) {
      await open(conversations.value[0].id);
    }
  } catch (e: any) {
    error.value = e.message;
  }
  pollTimer = setInterval(poll, 10000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

async function open(id: number) {
  activeId.value = id;
  const c = conversations.value.find((x) => x.id === id);
  activeTitle.value = c?.title || "Family";
  messages.value = await api(`/care/conversations/${id}/messages`);
  scrollDown();
}

async function poll() {
  if (!activeId.value) return;
  const rows = await api(`/care/conversations/${activeId.value}/messages`);
  if (rows.length !== messages.value.length) {
    messages.value = rows;
    scrollDown();
  }
}

const scrollDown = async () => {
  await nextTick();
  chatsEl.value?.scrollTo({ top: chatsEl.value.scrollHeight, behavior: "smooth" });
};

async function send(text?: string) {
  const content = (text ?? input.value).trim();
  if (!content || !activeId.value || loading.value) return;
  input.value = "";
  loading.value = true;
  try {
    const msg = await api(`/care/conversations/${activeId.value}/messages`, {
      method: "POST",
      body: { content },
    });
    messages.value.push(msg);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
    scrollDown();
  }
}
</script>

<template>
  <div class="flex h-[calc(100vh-180px)] flex-col">
    <div class="mb-2 flex items-center justify-between gap-2">
      <div class="flex min-w-0 items-center gap-3">
        <span class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-teal text-xs font-extrabold text-white">Family</span>
        <div class="min-w-0">
          <h2 class="truncate text-xl font-extrabold">{{ activeTitle || "Family chat" }}</h2>
          <p class="text-xs font-bold text-teal">All family members can see this</p>
        </div>
      </div>
      <button class="rounded-2xl bg-white px-3 py-2 text-sm font-extrabold shadow-card" title="Members">Members</button>
    </div>

    <p v-if="error" class="mb-2 rounded-2xl bg-rose/10 px-4 py-2 text-sm font-semibold text-rose">{{ error }}</p>

    <!-- Thread -->
    <div ref="chatsEl" class="flex-1 space-y-3 overflow-y-auto pr-1">
      <div v-if="!messages.length" class="rounded-3xl bg-teal p-5 text-white shadow-soft">
        <span class="inline-block rounded-2xl bg-white/15 px-4 py-1.5 text-sm font-extrabold">Family</span>
        <h3 class="mt-2 text-lg font-extrabold">Say hello to your family</h3>
        <p class="mt-1 text-sm text-teal-light">Share how you're doing — they care about every detail.</p>
      </div>

      <div v-for="m in messages" :key="m.id" class="flex" :class="m.sender_id === auth.user?.id ? 'justify-end' : 'justify-start'">
        <div
          class="max-w-[80%] rounded-3xl px-4 py-3"
          :class="m.sender_id === auth.user?.id ? 'bg-teal text-white' : 'bg-white shadow-card'"
        >
          <p v-if="m.sender_id !== auth.user?.id" class="mb-1 text-xs font-extrabold text-teal-dark">{{ m.sender_name }}</p>
          <p class="whitespace-pre-wrap text-[1.02rem] leading-relaxed">{{ m.content }}</p>
          <p class="mt-1 text-right text-[0.7rem]" :class="m.sender_id === auth.user?.id ? 'text-teal-light' : 'text-ink/40'">
            {{ fmtTime(m.created_at) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Quick chips -->
    <div class="mb-2 mt-2 flex flex-wrap gap-2">
      <button
        v-for="c in chips"
        :key="c"
        class="rounded-2xl bg-teal-light px-3 py-2 text-xs font-bold text-teal-dark transition hover:bg-teal/20"
        @click="send(c)"
      >
        {{ c }}
      </button>
    </div>

    <!-- Input -->
    <form class="flex gap-2" @submit.prevent="send()">
      <input v-model="input" class="input flex-1" placeholder="Type a message…" />
      <button type="submit" class="btn-primary px-6" :disabled="loading">Send</button>
    </form>
  </div>
</template>
