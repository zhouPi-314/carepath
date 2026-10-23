<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted } from "vue";
import { useRouter } from "vue-router";

import { defaultSectionForRole, roleLabel, sectionLabels } from "../lib/navigation";
import { useSessionStore } from "../stores/session";
const AdminPanel = defineAsyncComponent(() => import("../components/AdminPanel.vue"));
const DoctorPanel = defineAsyncComponent(() => import("../components/DoctorPanel.vue"));
const GovernmentPanel = defineAsyncComponent(
  () => import("../components/GovernmentPanel.vue"),
);
const HospitalPanel = defineAsyncComponent(() => import("../components/HospitalPanel.vue"));
const PatientPanel = defineAsyncComponent(() => import("../components/PatientPanel.vue"));
const PharmaPanel = defineAsyncComponent(() => import("../components/PharmaPanel.vue"));
const CommunityPanel = defineAsyncComponent(
  () => import("../components/CommunityPanel.vue"),
);
const HospitalOpsPanel = defineAsyncComponent(
  () => import("../components/HospitalOpsPanel.vue"),
);

const session = useSessionStore();
const router = useRouter();

const section = computed(() =>
  session.user ? defaultSectionForRole(session.user.role) : "patient",
);

const panels = {
  patient: PatientPanel,
  doctor: DoctorPanel,
  hospital: HospitalPanel,
  government: GovernmentPanel,
  pharma: PharmaPanel,
  community: CommunityPanel,
  admin: AdminPanel,
};

const panel = computed(() => panels[section.value]);

onMounted(async () => {
  await session.restore();
  if (!session.user) await router.replace("/login");
});

async function logout() {
  await session.logout();
  await router.replace("/login");
}
</script>

<template>
  <div v-if="session.user" class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-mark" aria-hidden="true">医</div>
        <div>
          <strong>治疗方案协同平台</strong>
          <span>Treatment Plan Coordination</span>
        </div>
      </div>

      <nav aria-label="工作台导航">
        <a class="nav-item active" href="#workspace">
          <span class="nav-index">01</span>
          {{ sectionLabels[section] }}
        </a>
      </nav>

      <div class="sidebar-note">
        <span>演示环境</span>
        <p>合成病例 · 沙箱权限 · 非生产医疗系统</p>
      </div>
    </aside>

    <div class="main-column">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ roleLabel(session.user.role) }} workspace</p>
          <strong>{{ session.user.displayName }}</strong>
          <span v-if="session.user.identityLabel" class="identity-badge">
            {{ session.user.identityLabel }}
          </span>
          <span v-if="session.user.organizationName" class="org-name">
            · {{ session.user.organizationName }}
          </span>
        </div>
        <div class="topbar-actions">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API 文档
          </a>
          <button type="button" class="logout" @click="logout">退出</button>
        </div>
      </header>

      <div class="safety-banner">
        本系统仅用于课程与竞赛演示。所有病例均为合成数据，不提供诊断、处方、医保结算或行政监管结论。
      </div>

      <main id="workspace" class="workspace">
        <component :is="panel" :key="section" />
        <HospitalOpsPanel v-if="section === 'hospital'" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 26px 20px;
  color: #eaf8f4;
  background:
    linear-gradient(180deg, #133f44, #0c2d31 72%),
    #0c2d31;
  display: flex;
  flex-direction: column;
}

.brand-block {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 0 8px 30px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px 12px 12px 3px;
  background: #efc47f;
  color: #173437;
  display: grid;
  place-items: center;
  font-size: 21px;
  font-weight: 900;
}

.brand-block strong,
.brand-block span {
  display: block;
}

.brand-block strong {
  font-size: 16px;
}

.brand-block span {
  color: #92bcb5;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

nav {
  display: grid;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: 12px;
  color: #d7ebe7;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.055);
}

.nav-index {
  color: #efc47f;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
}

.sidebar-note {
  margin-top: auto;
  border-top: 1px solid rgba(226, 247, 241, 0.15);
  padding: 18px 8px 0;
}

.sidebar-note span {
  color: #efc47f;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.sidebar-note p {
  color: #9fc2bc;
  font-size: 12px;
  line-height: 1.65;
}

.main-column {
  min-width: 0;
}

.topbar {
  min-height: 74px;
  padding: 12px clamp(20px, 4vw, 46px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.82);
  border-bottom: 1px solid var(--cp-line);
  backdrop-filter: blur(16px);
}

.topbar strong {
  margin-left: 8px;
}

.org-name {
  color: var(--cp-muted);
  font-size: 13px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.topbar-actions a {
  color: var(--cp-primary);
  font-size: 13px;
  text-decoration: none;
}

.logout {
  border: 1px solid var(--cp-line);
  background: white;
  border-radius: 10px;
  padding: 8px 13px;
  cursor: pointer;
}

.safety-banner {
  padding: 10px clamp(20px, 4vw, 46px);
  background: #fff7e9;
  border-bottom: 1px solid #ead8b6;
  color: #72501f;
  font-size: 12px;
  line-height: 1.65;
}

.workspace {
  padding: clamp(22px, 4vw, 46px);
}

@media (max-width: 820px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    height: auto;
    padding: 16px 18px;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .brand-block {
    padding: 0;
  }

  .nav-item,
  .sidebar-note {
    display: none;
  }
}

@media (max-width: 600px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .topbar-actions {
    width: 100%;
    justify-content: space-between;
  }
}
.identity-badge {
  margin-left: 8px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--cp-primary-soft);
  color: var(--cp-primary);
  font-size: 11px;
  font-weight: 700;
}
</style>
