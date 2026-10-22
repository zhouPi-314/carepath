<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";
import {
  alertStatusLabels,
  formatDateTime,
  taskStatusLabels,
} from "../lib/format";
import type { PatientDashboardData } from "../types";

const data = ref<PatientDashboardData | null>(null);
const loading = ref(true);
const error = ref("");
const completing = ref<string | null>(null);

const completedCount = computed(
  () => data.value?.tasks.filter((task) => task.status === "COMPLETED").length ?? 0,
);
const completionRate = computed(() => {
  const total = data.value?.tasks.length ?? 0;
  return total ? Math.round((completedCount.value / total) * 100) : 0;
});
const nextTask = computed(
  () => data.value?.tasks.find((task) => task.status !== "COMPLETED"),
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await apiRequest<PatientDashboardData>("/patient/dashboard");
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

async function completeTask(taskId: string) {
  completing.value = taskId;
  try {
    await apiRequest(`/tasks/${taskId}/complete`, {
      method: "POST",
      body: JSON.stringify({ note: "患者在演示端完成任务" }),
    });
    ElMessage.success("任务已同步，医生端可收到更新。");
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  } finally {
    completing.value = null;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header class="panel-header">
      <div>
        <p class="eyebrow">Treatment journey</p>
        <h1 class="page-heading">
          {{ data?.patient.displayName ?? "患者" }}的治疗进度
        </h1>
        <p class="page-subtitle">
          <template v-if="data?.plan">
            {{ data.plan.title }} · 版本 V{{ data.plan.version }}
          </template>
          <template v-else>暂无已发布计划</template>
        </p>
      </div>
      <el-tag type="success" effect="plain">患者已确认</el-tag>
    </header>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />

    <template v-if="data">
      <section class="hero-grid">
        <article class="journey-card">
          <div class="journey-copy">
            <p class="eyebrow">Next action</p>
            <h2>{{ nextTask?.title ?? "当前任务全部完成" }}</h2>
            <p>
              {{ nextTask?.description ?? "保持当前节奏，等待下一次随访。" }}
            </p>
            <el-button
              v-if="nextTask"
              type="primary"
              :loading="completing === nextTask.id"
              @click="completeTask(nextTask.id)"
            >
              标记为已完成
            </el-button>
          </div>
          <div class="progress-ring" :style="{ '--progress': `${completionRate}%` }">
            <strong>{{ completionRate }}%</strong>
            <span>任务完成</span>
          </div>
        </article>

        <article class="care-team card">
          <p class="eyebrow">Authorized care circle</p>
          <h2>授权照护者</h2>
          <div
            v-for="caregiver in data.caregivers"
            :key="caregiver.caregiverUserId"
            class="caregiver-row"
          >
            <span class="avatar">{{ caregiver.displayName.slice(0, 1) }}</span>
            <div>
              <strong>{{ caregiver.displayName }}</strong>
              <p>{{ caregiver.scopes.length }} 项授权 · 至 {{ formatDateTime(caregiver.expiresAt) }}</p>
            </div>
          </div>
          <p v-if="!data.caregivers.length" class="muted">尚未授权家属协同。</p>
        </article>
      </section>

      <div class="metric-grid">
        <div class="metric">
          <strong>{{ data.tasks.length }}</strong>
          <span>治疗任务总数</span>
        </div>
        <div class="metric">
          <strong>{{ completedCount }}</strong>
          <span>已完成任务</span>
        </div>
        <div class="metric">
          <strong>{{ data.medications.length }}</strong>
          <span>当前用药安排</span>
        </div>
        <div class="metric">
          <strong>{{ data.alerts.filter((item) => item.status === "OPEN").length }}</strong>
          <span>待处理提醒</span>
        </div>
      </div>

      <div class="split-grid">
        <section class="card">
          <div class="section-title">
            <div>
              <p class="eyebrow">Care tasks</p>
              <h2>协同任务</h2>
            </div>
            <span class="muted">按截止时间排序</span>
          </div>
          <div class="task-list">
            <article
              v-for="task in data.tasks"
              :key="task.id"
              class="task-row"
              :class="{ overdue: task.isOverdue, done: task.status === 'COMPLETED' }"
            >
              <div class="task-status" aria-hidden="true"></div>
              <div class="task-copy">
                <strong>{{ task.title }}</strong>
                <p>{{ task.description }}</p>
                <span>{{ formatDateTime(task.dueAt) }} · {{ task.category }}</span>
              </div>
              <div class="task-actions">
                <el-tag
                  :type="task.status === 'COMPLETED' ? 'success' : task.isOverdue ? 'danger' : 'warning'"
                  effect="plain"
                >
                  {{ task.isOverdue ? "已逾期" : taskStatusLabels[task.status] }}
                </el-tag>
                <el-button
                  v-if="task.status !== 'COMPLETED'"
                  text
                  type="primary"
                  @click="completeTask(task.id)"
                >
                  完成
                </el-button>
              </div>
            </article>
          </div>
        </section>

        <div class="panel-stack">
          <section class="card">
            <p class="eyebrow">Medication schedule</p>
            <h2>用药安排</h2>
            <div class="med-list">
              <div v-for="med in data.medications" :key="med.id" class="med-row">
                <span class="med-mark">Rx</span>
                <div>
                  <strong>{{ med.drugName }}</strong>
                  <p>{{ med.doseText }} · {{ med.frequencyText }}</p>
                </div>
              </div>
            </div>
            <p class="safety-note">仅展示计划与自报记录，不提供处方或剂量调整。</p>
          </section>

          <section class="card">
            <p class="eyebrow">Alerts</p>
            <h2>异常提醒</h2>
            <article v-for="alert in data.alerts" :key="alert.id" class="alert-row">
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
            <p v-if="!data.alerts.length" class="muted">暂无提醒。</p>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel-header,
.section-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 0.8fr);
  gap: 18px;
}

.journey-card {
  min-height: 230px;
  border-radius: 22px;
  padding: clamp(24px, 4vw, 38px);
  background:
    linear-gradient(135deg, rgba(13, 92, 99, 0.98), rgba(17, 65, 69, 0.99));
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
}

.journey-copy {
  max-width: 580px;
}

.journey-card .eyebrow {
  color: #f0c47f;
}

.journey-card h2 {
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.18;
  letter-spacing: -0.04em;
  margin: 12px 0;
}

.journey-card p:not(.eyebrow) {
  color: #c5e1dc;
  line-height: 1.7;
  margin-bottom: 22px;
}

.progress-ring {
  --progress: 0%;
  flex: 0 0 132px;
  width: 132px;
  height: 132px;
  border-radius: 50%;
  display: grid;
  place-content: center;
  text-align: center;
  background: conic-gradient(#efc47f var(--progress), rgba(255, 255, 255, 0.13) 0);
  position: relative;
}

.progress-ring::after {
  content: "";
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  background: #164b50;
}

.progress-ring strong,
.progress-ring span {
  position: relative;
  z-index: 1;
}

.progress-ring strong {
  font-size: 28px;
}

.progress-ring span {
  color: #b7d6d0;
  font-size: 11px;
}

.care-team h2 {
  margin-bottom: 18px;
}

.caregiver-row,
.med-row,
.alert-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 0;
  border-top: 1px solid #edf3f1;
}

.caregiver-row:first-of-type,
.med-row:first-child,
.alert-row:first-child {
  border-top: 0;
}

.caregiver-row p,
.med-row p,
.alert-row p {
  color: var(--cp-muted);
  margin: 4px 0;
  font-size: 12px;
  line-height: 1.55;
}

.avatar,
.med-mark {
  flex: 0 0 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--cp-primary-soft);
  color: var(--cp-primary);
  font-size: 12px;
  font-weight: 800;
}

.section-title h2 {
  margin: 4px 0 0;
}

.task-list {
  display: grid;
  margin-top: 18px;
}

.task-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  min-height: 84px;
  border-top: 1px solid #edf3f1;
}

.task-row:first-child {
  border-top: 0;
}

.task-status {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #c8d8d4;
}

.task-row.overdue .task-status {
  background: var(--cp-danger);
}

.task-row.done .task-status {
  background: #4d9f7f;
}

.task-copy strong {
  display: block;
}

.task-copy p {
  color: var(--cp-muted);
  margin: 4px 0;
  font-size: 13px;
}

.task-copy span {
  color: #7b8d8f;
  font-size: 11px;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert-row span:not(.status-dot) {
  color: var(--cp-muted);
  font-size: 11px;
}

.safety-note {
  background: #f7faf9;
  border-radius: 10px;
  color: var(--cp-muted);
  font-size: 12px;
  line-height: 1.55;
  padding: 10px 12px;
}

@media (max-width: 1100px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .journey-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .task-row {
    grid-template-columns: 10px minmax(0, 1fr);
    padding: 12px 0;
  }

  .task-actions {
    grid-column: 2;
    justify-content: space-between;
  }
}
</style>
