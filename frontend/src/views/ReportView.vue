<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api, fmtDay } from "@/services/api";
import { useI18n } from "@/i18n";

const router = useRouter();
const { t, isZh } = useI18n();
const reports = ref<any[]>([]);
const loading = ref(true);
const uploading = ref(false);
const error = ref("");
const done = ref("");

// upload form
const showForm = ref(false);
const title = ref("");
const type = ref("lab");
const date = ref(new Date().toISOString().slice(0, 10));
const file = ref<File | null>(null);

// expanded detail
const openId = ref<number | null>(null);
const detail = ref<any>(null);

const TYPES: Record<string, { key: string; icon: string }> = {
  lab: { key: "rep.typeLab", icon: "LAB" },
  blood: { key: "rep.typeBlood", icon: "BLD" },
  imaging: { key: "rep.typeImaging", icon: "IMG" },
  discharge: { key: "rep.typeDischarge", icon: "DIS" },
  other: { key: "rep.typeOther", icon: "DOC" },
};

const flagStyle = (flag: string) => {
  if (flag === "normal") return "text-teal-dark bg-teal-light";
  if (flag === "low") return "text-amber bg-amber-light";
  if (flag === "high" || flag === "critical") return "text-rose bg-rose/10";
  return "text-ink/60 bg-cream";
};

const flagLabel = (flag: string) =>
  flag === "normal" ? t("rep.flagOk") : flag === "low" ? t("rep.flagLow") : flag === "high" ? t("rep.flagHigh") : t("rep.flagCritical");

const pickFile = (e: Event) => {
  const el = e.target as HTMLInputElement;
  file.value = el.files?.[0] ?? null;
};

onMounted(load);

async function load() {
  try {
    reports.value = await api("/reports");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function upload() {
  error.value = "";
  done.value = "";
  if (!file.value) {
    error.value = t("rep.fileNeeded");
    return;
  }
  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    fd.append("title", title.value || file.value.name);
    fd.append("report_type", type.value);
    fd.append("report_date", date.value);
    const created = await api("/reports/upload", { method: "POST", formData: fd });
    reports.value = [created, ...reports.value];
    showForm.value = false;
    title.value = "";
    file.value = null;
    done.value = t("rep.uploaded", { title: created.title });
    await toggle(created.id);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    uploading.value = false;
  }
}

async function toggle(id: number) {
  if (openId.value === id) {
    openId.value = null;
    detail.value = null;
    return;
  }
  openId.value = id;
  detail.value = null;
  try {
    detail.value = await api(`/reports/${id}`);
  } catch (e: any) {
    console.error(e);
  }
}

async function shareWithFamily(r: any) {
  done.value = "";
  try {
    const convs = await api("/care/conversations");
    if (!convs.length) {
      error.value = t("rep.noConv");
      return;
    }
    const snippet = (r.summary || "").slice(0, 140);
    const prefix = isZh.value
      ? `我的报告「${r.title}」（${fmtDay(r.report_date)}）：`
      : `My report "${r.title}" (${fmtDay(r.report_date)}): `;
    await api(`/care/conversations/${convs[0].id}/messages`, {
      method: "POST",
      body: { content: `${prefix}${snippet}` },
    });
    done.value = t("rep.shared");
    router.push("/app/chat");
  } catch (e: any) {
    error.value = e.message;
  }
}

function askCareMind(r: any) {
  sessionStorage.setItem(
    "caremind_question",
    isZh.value
      ? `请用大白话解释我的报告「${r.title}」（${fmtDay(r.report_date)}）— 有什么需要和医生讨论的吗？`
      : `Please explain my report "${r.title}" (${fmtDay(r.report_date)}) in simple words — anything I should discuss with my doctor?`,
  );
  router.push("/app/ai");
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-extrabold">{{ t("rep.title") }}</h2>
        <p class="text-sm text-ink/60">{{ t("rep.sub") }}</p>
      </div>
      <button class="btn-primary" @click="showForm = !showForm">{{ showForm ? t("rep.cancel") : "+ " + t("rep.upload") }}</button>
    </div>

    <p v-if="done" class="rounded-2xl bg-teal-light px-4 py-3 font-bold text-teal-dark">{{ done }}</p>
    <p v-if="error" class="rounded-2xl bg-rose/10 px-4 py-3 font-semibold text-rose">{{ error }}</p>

    <!-- Upload form -->
    <div v-if="showForm" class="card space-y-4">
      <h3 class="text-lg font-extrabold">{{ t("rep.uploadTitle") }}</h3>
      <div>
        <label class="label">{{ t("rep.fileLabel") }}</label>
        <label
          class="mt-1 flex cursor-pointer items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-teal/40 bg-teal-light/50 px-4 py-6 text-center font-bold text-teal-dark transition hover:bg-teal-light"
        >
          <span>{{ file ? file.name : t("rep.chooseFile") }}</span>
          <input type="file" accept=".pdf,.png,.jpg,.jpeg" class="hidden" @change="pickFile" />
        </label>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ t("rep.reportType") }}</label>
          <select v-model="type" class="input mt-1">
            <option v-for="(v, k) in TYPES" :key="k" :value="k">{{ t(v.key) }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ t("rep.date") }}</label>
          <input v-model="date" type="date" class="input mt-1" />
        </div>
      </div>
      <div>
        <label class="label">{{ t("rep.titleField") }}</label>
        <input v-model="title" class="input mt-1" :placeholder="t('rep.titlePh')" />
      </div>
      <button class="btn-primary w-full" :disabled="uploading" @click="upload">
        {{ uploading ? t("rep.analyzing") : t("rep.uploadAnalyze") }}
      </button>
      <p class="text-xs text-ink/50">{{ t("rep.demoNote") }}</p>
    </div>

    <!-- Reports list -->
    <div v-if="loading" class="py-16 text-center text-ink/50">{{ t("common.loading") }}</div>

    <div v-else-if="!reports.length && !showForm" class="card py-10 text-center">
      <p class="mt-3 font-extrabold text-lg">{{ t("rep.empty") }}</p>
      <p class="mt-1 text-ink/60">{{ t("rep.emptySub") }}</p>
    </div>

    <div v-for="r in reports" :key="r.id" class="card">
      <button class="flex w-full items-center gap-4 text-left" @click="toggle(r.id)">
        <span class="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-teal-light text-xs font-extrabold text-teal-dark">
          {{ TYPES[r.report_type]?.icon || "DOC" }}
        </span>
        <div class="min-w-0 flex-1">
          <p class="font-extrabold text-lg leading-snug">{{ r.title }}</p>
          <p class="text-sm text-ink/60">{{ fmtDay(r.report_date) }} · {{ t(TYPES[r.report_type]?.key || "rep.typeOther") }}</p>
        </div>
        <div class="text-ink/40 text-xl">{{ openId === r.id ? "▾" : "▸" }}</div>
      </button>

      <p v-if="r.summary" class="mt-3 rounded-2xl bg-cream px-4 py-3 text-sm leading-relaxed text-ink/80">
        <b class="text-teal-dark">{{ t("rep.careMindSays") }}</b> {{ r.summary }}
      </p>

      <!-- Detail -->
      <div v-if="openId === r.id" class="mt-4 space-y-3">
        <div v-if="!detail" class="py-6 text-center text-ink/50">{{ t("rep.reading") }}</div>
        <template v-else>
          <div class="overflow-hidden rounded-3xl border border-ink/10">
            <table class="w-full text-left text-sm">
              <thead class="bg-cream text-xs font-bold uppercase text-ink/50">
                <tr>
                  <th class="px-4 py-3">{{ t("rep.test") }}</th>
                  <th class="px-3 py-3">{{ t("rep.result") }}</th>
                  <th class="px-3 py-3">{{ t("rep.range") }}</th>
                  <th class="px-4 py-3 text-right">{{ t("rep.flag") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detail.results" :key="row.item_name" class="border-t border-ink/5">
                  <td class="px-4 py-3 font-bold">{{ row.item_name }}</td>
                  <td class="px-3 py-3 font-extrabold">{{ row.result_value }} <span class="text-xs font-semibold text-ink/50">{{ row.unit }}</span></td>
                  <td class="px-3 py-3 text-ink/60">{{ row.reference_range }}</td>
                  <td class="px-4 py-3 text-right">
                    <span class="rounded-xl px-3 py-1 text-xs font-extrabold" :class="flagStyle(row.flag)">{{ flagLabel(row.flag) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-ink/50">{{ t("rep.note") }}</p>
          <div class="flex gap-3">
            <button class="btn-primary flex-1" @click="askCareMind(r)">{{ t("rep.explain") }}</button>
            <button class="btn-ghost flex-1" @click="shareWithFamily(r)">{{ t("rep.shareFamily") }}</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>