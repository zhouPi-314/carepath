<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiRequest, explainApiError } from "../lib/api";
import { alertStatusLabels, formatDateTime, formatPercent } from "../lib/format";
import type { HospitalDashboardData } from "../types";
import { useSessionStore } from "../stores/session";

interface Member {
  id: string;
  username: string;
  displayName: string;
  role: string;
  active: boolean;
}

const session = useSessionStore();
const data = ref<HospitalDashboardData | null>(null);
const members = ref<Member[]>([]);
const error = ref("");
const loading = ref(true);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await apiRequest<HospitalDashboardData>("/hospital/dashboard");
    if (session.user?.organizationId) {
      members.value = await apiRequest<Member[]>(
        `/organizations/${session.user.organizationId}/members`,
      );
    }
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header>
      <p class="eyebrow">Hospital operations</p>
      <h1 class="page-heading">医院协同中心</h1>
      <p class="page-subtitle">
        {{ data?.organization.name ?? "机构" }} · 仅展示本院范围内的治疗计划与人员。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="data" class="metric-grid">
      <div class="metric">
        <strong>{{ data.activePlans }}</strong>
        <span>活跃协同计划</span>
      </div>
      <div class="metric">
        <strong>{{ data.doctorCount }}</strong>
        <span>在岗医生</span>
      </div>
      <div class="metric">
        <strong>{{ formatPercent(data.taskCompletionRate) }}</strong>
        <span>任务完成率</span>
      </div>
      <div class="metric">
        <strong>{{ data.openAlerts }}</strong>
        <span>待处理提醒</span>
      </div>
    </div>

    <div class="split-grid">
      <section class="card">
        <div class="section-title">
          <div>
            <p class="eyebrow">Care team</p>
            <h2>院内协同成员</h2>
          </div>
          <span class="muted">{{ members.length }} 人</span>
        </div>
        <el-table :data="members" class="member-table">
          <el-table-column prop="displayName" label="姓名" min-width="130" />
          <el-table-column prop="role" label="角色" width="150" />
          <el-table-column prop="username" label="账号" min-width="140" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.active ? 'success' : 'info'" effect="plain">
                {{ row.active ? "启用" : "停用" }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="card">
        <p class="eyebrow">Recent alerts</p>
        <h2>近期协同提醒</h2>
        <article v-for="alert in data?.recentAlerts" :key="alert.id" class="alert-row">
          <span
            class="status-dot"
            :class="{ danger: alert.severity === 'HIGH', warn: alert.severity === 'MEDIUM' }"
          ></span>
          <div>
            <strong>{{ alert.title }}</strong>
            <p>{{ alert.detail }}</p>
            <span>{{ alertStatusLabels[alert.status] }} · {{ formatDateTime(alert.createdAt) }}</span>
          </div>
        </article>
        <p v-if="!data?.recentAlerts.length" class="empty-state">暂无提醒。</p>
        <p class="boundary-note">
          医院管理员可查看本院运营数据，但不能通过该页面浏览其他机构或导出患者明细。
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.section-title h2 {
  margin: 4px 0 18px;
}

.member-table {
  --el-table-border-color: #e3ece9;
  --el-table-header-bg-color: #f5f9f8;
}

.alert-row {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid #edf3f1;
}

.alert-row:first-of-type {
  border-top: 0;
}

.alert-row p {
  color: var(--cp-muted);
  font-size: 12px;
  line-height: 1.6;
  margin: 4px 0;
}

.alert-row span:not(.status-dot) {
  color: var(--cp-muted);
  font-size: 11px;
}

.boundary-note {
  color: var(--cp-muted);
  background: #f7faf9;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.65;
  padding: 11px 12px;
}
</style>
