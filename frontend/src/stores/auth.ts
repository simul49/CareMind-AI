import { defineStore } from "pinia";
import { api } from "@/services/api";

export interface User {
  id: number;
  full_name: string;
  email?: string;
  phone?: string;
  role: string;
  date_of_birth?: string;
  gender?: string;
  city?: string;
  avatar_url?: string;
  is_accessible_mode?: boolean;
}

interface AuthResponse {
  access_token: string;
  user: User;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("caremind_token") as string | null,
    user: JSON.parse(localStorage.getItem("caremind_user") || "null") as User | null,
  }),
  actions: {
    async login(email: string, password: string) {
      const data = await api<AuthResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      this._setSession(data);
    },
    async register(payload: Record<string, any>) {
      const data = await api<AuthResponse>("/auth/register", {
        method: "POST",
        body: payload,
      });
      this._setSession(data);
    },
    _setSession(data: AuthResponse) {
      this.token = data.access_token;
      this.user = data.user;
      localStorage.setItem("caremind_token", data.access_token);
      localStorage.setItem("caremind_user", JSON.stringify(data.user));
    },
    async refresh() {
      if (!this.token) return;
      try {
        const me = await api<User>("/auth/me");
        this.user = me;
        localStorage.setItem("caremind_user", JSON.stringify(me));
      } catch {
        this.logout();
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("caremind_token");
      localStorage.removeItem("caremind_user");
    },
  },
});
