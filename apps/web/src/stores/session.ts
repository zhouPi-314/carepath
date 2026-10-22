import { defineStore } from "pinia";

import { apiRequest } from "../lib/api";
import type { LoginResponse, User } from "../types";

const USER_KEY = "carepath.user";
const CSRF_KEY = "carepath.csrf";

function storedUser(): User | null {
  const raw = sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    sessionStorage.removeItem(USER_KEY);
    return null;
  }
}

export const useSessionStore = defineStore("session", {
  state: () => ({
    user: storedUser(),
    loading: false,
  }),
  getters: {
    authenticated: (state) => Boolean(state.user),
  },
  actions: {
    async login(username: string, password: string) {
      this.loading = true;
      try {
        const payload = await apiRequest<LoginResponse>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        this.user = payload.user;
        sessionStorage.setItem(USER_KEY, JSON.stringify(payload.user));
        sessionStorage.setItem(CSRF_KEY, payload.csrfToken);
      } finally {
        this.loading = false;
      }
    },
    async restore() {
      if (this.user) return;
      try {
        const user = await apiRequest<User>("/auth/me");
        this.user = user;
        sessionStorage.setItem(USER_KEY, JSON.stringify(user));
      } catch {
        this.user = null;
      }
    },
    async logout() {
      try {
        await apiRequest("/auth/logout", { method: "POST" });
      } finally {
        this.user = null;
        sessionStorage.removeItem(USER_KEY);
        sessionStorage.removeItem(CSRF_KEY);
      }
    },
  },
});
