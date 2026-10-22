import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "./views/DashboardView.vue";
import LoginView from "./views/LoginView.vue";
import { useSessionStore } from "./stores/session";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { public: true },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: DashboardView,
    },
    { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
  ],
});

router.beforeEach((to) => {
  const session = useSessionStore();
  if (!to.meta.public && !session.authenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.name === "login" && session.authenticated) {
    return { name: "dashboard" };
  }
  return true;
});
