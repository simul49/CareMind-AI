// Lightweight hand-rolled i18n for CareMind (English + 简体中文).
// No external dependency — keeps the build robust on flaky networks.
import { computed, ref } from "vue";
import { en } from "./en";
import { zh } from "./zh";

export type Locale = "en" | "zh";

const STORAGE_KEY = "caremind_locale";

const dictionaries = { en, zh } as const;

const locale = ref<Locale>((localStorage.getItem(STORAGE_KEY) as Locale) || "en");

export function setLocale(l: Locale) {
  locale.value = l;
  localStorage.setItem(STORAGE_KEY, l);
  document.documentElement.lang = l === "zh" ? "zh-CN" : "en";
}

export function t(path: string, params?: Record<string, string | number>): string {
  let cur: any = dictionaries[locale.value];
  for (const part of path.split(".")) {
    if (cur == null) return path;
    cur = cur[part];
  }
  if (typeof cur !== "string") return path;
  if (params) {
    return cur.replace(/\{(\w+)\}/g, (_, k: string) =>
      params[k] !== undefined ? String(params[k]) : `{${k}}`,
    );
  }
  return cur;
}

export const isZh = computed(() => locale.value === "zh");
export const jsLocale = computed(() => (locale.value === "zh" ? "zh-CN" : "en-US"));

export function useI18n() {
  return { locale, isZh, setLocale, t };
}

// ---- locale-aware date helpers (shared with services/api.ts) ----

export function fmtTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString(jsLocale.value, { hour: "2-digit", minute: "2-digit" });
}

export function fmtDay(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(jsLocale.value, { month: "short", day: "numeric" });
}
