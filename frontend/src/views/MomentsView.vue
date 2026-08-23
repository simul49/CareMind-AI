<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/services/api";

const posts = ref<any[]>([]);
const newPost = ref("");
const sending = ref(false);

onMounted(async () => {
  try {
    posts.value = await api("/care/posts");
  } catch (e) {
    console.error(e);
  }
});

const post = async () => {
  if (!newPost.value.trim() || sending.value) return;
  sending.value = true;
  try {
    const created = await api("/care/posts", { method: "POST", body: { content: newPost.value } });
    posts.value.unshift(created);
    newPost.value = "";
  } finally {
    sending.value = false;
  }
};

const toggleReact = async (p: any) => {
  const res = await api(`/care/posts/${p.id}/react`, { method: "POST" });
  p.my_reaction = res.reacted ? "like" : null;
  p.reaction_count += res.reacted ? 1 : -1;
};
</script>

<template>
  <div class="space-y-4">
    <div class="card">
      <p class="label">Share a moment</p>
      <textarea v-model="newPost" rows="2" class="input mt-2 resize-none"
                placeholder="How was your day? What made you smile today?"></textarea>
      <button class="btn-primary mt-3 w-full" :disabled="sending" @click="post">Share</button>
    </div>

    <div v-for="p in posts" :key="p.id" class="card">
      <div class="flex items-center gap-3">
        <div class="grid h-11 w-11 place-items-center rounded-full bg-teal-light font-extrabold text-teal-dark">
          {{ p.author_name.split(" ").map((s: string) => s[0]).slice(0, 2).join("") }}
        </div>
        <div>
          <p class="font-extrabold">{{ p.author_name }}</p>
          <p class="text-xs text-ink/50">{{ new Date(p.created_at).toLocaleString() }}</p>
        </div>
      </div>
      <p class="mt-3 whitespace-pre-wrap text-[1.05rem] leading-relaxed">{{ p.content }}</p>
      <div class="mt-3 flex items-center gap-2">
        <button class="rounded-2xl px-4 py-2 font-bold transition"
                :class="p.my_reaction ? 'bg-rose/10 text-rose' : 'bg-cream text-ink/60'"
                @click="toggleReact(p)">
          {{ p.my_reaction ? "Loved" : "Love this" }} · {{ p.reaction_count }}
        </button>
        <span class="text-sm font-semibold text-ink/40">Care circle only</span>
      </div>
    </div>
  </div>
</template>
