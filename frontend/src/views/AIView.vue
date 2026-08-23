<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { api } from "@/services/api";

const messages = ref<any[]>([]);
const input = ref("");
const conversationId = ref<number | null>(null);
const loading = ref(false);
const chatsEl = ref<HTMLElement | null>(null);
const starterVisible = ref(true);

const chips = [
  "How is my blood pressure this week? 💙",
  "I'm feeling a little dizzy lately",
  "Remind me about my medicines",
  "What did I do for exercise this week?",
];

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
});

const scrollDown = async () => {
  await nextTick();
  chatsEl.value?.scrollTo({ top: chatsEl.value.scrollHeight, behavior: "smooth" });
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
      body: { conversation_id: conversationId.value, message: content },
    });
    conversationId.value = res.conversation_id;
    messages.value.push({
      id: Date.now() + 1,
      sender: "assistant",
      content: res.reply,
      created_at: new Date().toISOString(),
    });
  } catch (e: any) {
    messages.value.push({ id: Date.now() + 2, sender: "assistant", content: "Sorry, I couldn't reach my brain. Please try again.", created_at: new Date().toISOString() });
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
        <p class="text-2xl">🤖</p>
        <h3 class="mt-1 text-xl font-extrabold">Hi! I'm CareMind</h3>
        <p class="mt-1 text-teal-light">
          I'm your health companion. I know your health records, medicines and care plan —
          and I'm here to help you understand them. I never replace your doctor.
        </p>
      </div>

      <div v-for="m in messages" :key="m.id"
           :class="m.sender === 'user' ? 'ml-auto max-w-[80%] rounded-3xl bg-teal px-4 py-3 text-white' : 'mr-auto max-w-[85%] rounded-3xl bg-white px-4 py-3 shadow-card'">
        <p class="whitespace-pre-wrap text-[1.05rem] leading-relaxed">{{ m.content }}</p>
      </div>

      <div v-if="loading" class="mr-auto max-w-[85%] rounded-3xl bg-white px-4 py-3 shadow-card">
        <span class="text-ink/50">CareMind is typing<span class="animate-pulse">…</span></span>
      </div>
    </div>

    <div v-if="starterVisible" class="mb-2 flex flex-wrap gap-2">
      <button v-for="c in chips" :key="c" class="rounded-2xl bg-teal-light px-4 py-2 text-left text-sm font-bold text-teal-dark transition hover:bg-teal/20"
              @click="send(c)">{{ c }}</button>
    </div>

    <form class="flex gap-2" @submit.prevent="send()">
      <input v-model="input" class="input flex-1" placeholder="Type a message…" />
      <button type="submit" class="btn-primary px-6" :disabled="loading">Send</button>
    </form>
  </div>
</template>
