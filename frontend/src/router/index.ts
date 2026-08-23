import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "landing", component: () => import("@/views/LandingView.vue") },
    { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
    { path: "/register", name: "register", component: () => import("@/views/RegisterView.vue") },
    {
      path: "/app",
      component: () => import("@/layouts/ElderLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: "/app/home" },
        { path: "home", name: "home", component: () => import("@/views/ElderHomeView.vue") },
        { path: "health", name: "health", component: () => import("@/views/HealthView.vue") },
        { path: "medicines", name: "medicines", component: () => import("@/views/MedicinesView.vue") },
        { path: "ai", name: "ai", component: () => import("@/views/AIView.vue") },
        { path: "moments", name: "moments", component: () => import("@/views/MomentsView.vue") },
        { path: "emergency", name: "emergency", component: () => import("@/views/EmergencyView.vue") },
        { path: "profile", name: "profile", component: () => import("@/views/ProfileView.vue") },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if ((to.name === "login" || to.name === "register") && auth.token) {
    return { name: "home" };
  }
  return true;
});

export default router;
