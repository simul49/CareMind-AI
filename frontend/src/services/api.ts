const BASE = "/api";

export async function api<T = any>(
  path: string,
  options: { method?: string; body?: any; formData?: FormData } = {},
): Promise<T> {
  const token = localStorage.getItem("caremind_token");
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let body: any;
  if (options.formData) {
    body = options.formData;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  const res = await fetch(BASE + path, {
    method: options.method || "GET",
    headers,
    body,
  });

  if (res.status === 401) {
    localStorage.removeItem("caremind_token");
    localStorage.removeItem("caremind_user");
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : "Something went wrong";
    throw new Error(message);
  }
  return data as T;
}

export const fmtTime = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export const fmtDay = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
};
