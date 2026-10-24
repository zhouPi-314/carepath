<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { explainApiError } from "../lib/api";
import { roleLabel, type Role } from "../lib/navigation";
import { useSessionStore } from "../stores/session";
import AppIcon from "../components/AppIcon.vue";

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
type DemoAccount = { username: string; password: string; role: Role; summary: string };

const demoAccounts: DemoAccount[] = [
  { username: "patient", password: "Pa2026!care", role: "PATIENT", summary: "用户 / 居民统一入口，病患与家属由医院数据标识" },
  { username: "doctor", password: "Do2026!care", role: "DOCTOR", summary: "患者计划与提醒" },
  { username: "hospital", password: "Ho2026!care", role: "HOSPITAL_ADMIN", summary: "院内协同统计" },
  { username: "regulator", password: "Re2026!care", role: "REGULATOR", summary: "入驻认证与区域指标" },
  { username: "pharma", password: "Ph2026!care", role: "PHARMA", summary: "药品供应与产能" },
  { username: "community", password: "Co2026!care", role: "COMMUNITY_ORG", summary: "志愿调度与药品配送" },
  { username: "volunteer", password: "Vo2026!care", role: "VOLUNTEER", summary: "我的志愿任务与配送" },
];

const username = ref(demoAccounts[0].username);
const password = ref(demoAccounts[0].password);
const error = ref("");

function iconFor(role: Role) {
  if (role === "DOCTOR" || role === "HOSPITAL_ADMIN") return "hospital";
  if (role === "PHARMA") return "truck";
  if (role === "COMMUNITY_ORG") return "people";
  if (role === "REGULATOR") return "shield";
  return "heart";
}

function choose(account: DemoAccount) {
  username.value = account.username;
  password.value = account.password;
}

async function submit() {
  error.value = "";
  try {
    await session.login(username.value.trim(), password.value);
    const redirect =
      typeof route.query.redirect === "string" ? route.query.redirect : "/dashboard";
    await router.replace(redirect);
  } catch (caught) {
    error.value = explainApiError(caught);
    ElMessage.error(error.value);
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-story" aria-labelledby="product-title">
      <div class="brand-seal" aria-hidden="true">医</div>
      <p class="eyebrow">Medical & Health Collaboration</p>
      <h1 id="product-title">医疗健康保障协同平台</h1>
      <p class="tagline">
        把治疗计划、随访任务、家属授权与多方反馈放进同一条可追踪路径。
      </p>
      <div class="story-points">
        <span>五类角色协同</span>
        <span>版本化治疗计划</span>
        <span>脱敏聚合监管</span>
        <span>三端演示入口</span>
      </div>
      <p class="boundary">
        当前为工程化演示系统，使用合成病例与官方公开数据快照，不用于真实诊疗。
      </p>
    </section>

    <section class="login-panel" aria-labelledby="login-title">
      <div>
        <p class="eyebrow">Sandbox access</p>
        <h2 id="login-title">登录协同工作台</h2>
        <p class="page-subtitle">选择角色入口，账号与演示密码自动填入；登录后显示病患 / 家属等身份标识。</p>
      </div>

      <div class="role-grid" aria-label="演示角色">
        <button
          v-for="account in demoAccounts"
          :key="account.username"
          type="button"
          class="role-card"
          :class="{ selected: username === account.username }"
          @click="choose(account)"
        >
          <AppIcon class="role-icon" :name="iconFor(account.role)" :size="18" />
          <strong>{{ roleLabel(account.role) }}</strong>
          <span>{{ account.summary }}</span>
        </button>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label>
          <span>账号</span>
          <input v-model="username" autocomplete="username" required />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </label>
        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
        <el-button
          native-type="submit"
          type="primary"
          size="large"
          :loading="session.loading"
          class="login-button"
        >
          进入平台
        </el-button>
      </form>
      <p class="demo-password">演示密码：各角色不同，选择角色后自动填入。</p>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(420px, 0.95fr);
}

.login-story {
  padding: clamp(42px, 7vw, 96px);
  color: #effaf7;
  background:
    linear-gradient(145deg, rgba(13, 92, 99, 0.96), rgba(17, 54, 59, 0.98)),
    repeating-linear-gradient(
      120deg,
      transparent 0,
      transparent 40px,
      rgba(255, 255, 255, 0.035) 41px,
      rgba(255, 255, 255, 0.035) 42px
    );
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-seal {
  width: 64px;
  height: 64px;
  border-radius: 18px 18px 18px 4px;
  display: grid;
  place-items: center;
  background: #f3c784;
  color: #173437;
  font-size: 30px;
  font-weight: 900;
  margin-bottom: 30px;
}

.login-story .eyebrow {
  color: #b9e5da;
}

h1 {
  font-size: clamp(54px, 8vw, 92px);
  line-height: 0.96;
  letter-spacing: -0.07em;
  margin: 18px 0;
}

.tagline {
  font-size: clamp(18px, 2vw, 23px);
  line-height: 1.7;
  max-width: 620px;
  color: #d8efea;
}

.story-points {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 36px 0;
}

.story-points span {
  padding: 9px 13px;
  border: 1px solid rgba(222, 246, 240, 0.28);
  border-radius: 999px;
  font-size: 13px;
}

.boundary {
  max-width: 620px;
  color: #a8c9c4;
  font-size: 13px;
  line-height: 1.8;
}

.login-panel {
  background: rgba(255, 255, 255, 0.94);
  padding: clamp(30px, 5vw, 72px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
}

h2 {
  font-size: 34px;
  margin: 10px 0 0;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.role-card {
  align-items: center;
  justify-content: flex-start;
  text-align: left;
  border: 1px solid var(--cp-line);
  border-radius: 14px;
  padding: 14px;
  background: #fbfdfc;
  cursor: pointer;
  transition:
    border-color 160ms ease,
    transform 160ms ease;
}

.role-card:hover,
.role-card:focus-visible,
.role-card.selected {
  border-color: var(--cp-primary);
  transform: translateY(-1px);
  outline: none;
}

.role-card.selected {
  background: var(--cp-primary-soft);
}

.role-card strong,
.role-card span {
  display: block;
}

.role-card span {
  color: var(--cp-muted);
  font-size: 12px;
  margin-top: 5px;
}

.login-form {
  display: grid;
  gap: 16px;
}

.login-form label {
  display: grid;
  gap: 7px;
  font-size: 13px;
  font-weight: 700;
}

.login-form input {
  min-height: 46px;
  border: 1px solid #c9d9d5;
  border-radius: 11px;
  padding: 0 14px;
  background: white;
}

.login-form input:focus {
  outline: 3px solid rgba(13, 92, 99, 0.18);
  border-color: var(--cp-primary);
}

.login-button {
  width: 100%;
  min-height: 48px;
}

.form-error {
  color: var(--cp-danger);
  background: #fbebe8;
  border-radius: 10px;
  padding: 10px 12px;
  margin: 0;
}

.demo-password {
  color: var(--cp-muted);
  font-size: 12px;
  margin: -12px 0 0;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-story {
    min-height: 42vh;
  }
}

.role-icon {
  color: var(--cp-primary);
  flex: none;
  margin-top: 2px;
}
</style>