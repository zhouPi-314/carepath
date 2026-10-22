<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";
import { formatPercent } from "../lib/format";
import type { DoctorDashboardData } from "../types";

interface TemplateItem {
  id: string;
  name: string;
  conditionFocus: string;
  version: number;
  status: string;
  content: Record<string, unknown>;
}

const data = ref<DoctorDashboardData | null>(null);
const templates = ref<TemplateItem[]>([]);
const loading = ref(true);
const dialogOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({
  patientId: "",
  templateId: "",
  title: "",
  startDate: new Date().toISOString().slice(0, 10),
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [data.value, templates.value] = await Promise.all([
      apiRequest<DoctorDashboardData>("/doctor/dashboard"),
      apiRequest<TemplateItem[]>("/care-plan-templates"),
    ]);
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

function openCreate(patientId: string, patientName: string) {
  form.patientId = patientId;
  form.templateId = templates.value[0]?.id ?? "";
  form.title = `${patientName}的新版协同计划`;
  form.startDate = new Date().toISOString().slice(0, 10);
  dialogOpen.value = true;
}

async function createPlan() {
  saving.value = true;
  try {
    await apiRequest("/treatment-plans", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({
        patientId: form.patientId,
        templateId: form.templateId,
        title: form.title,
        startDate: form.startDate,
      }),
    });
    dialogOpen.value = false;
    ElMessage.success("新版治疗计划已创建，患者确认后进入协同。");
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header>
      <p class="eyebrow">Clinical coordination</p>
      <h1 class="page-heading">医生工作台</h1>
      <p class="page-subtitle">
        跟踪负责患者的计划进度、逾期任务和异常提醒；系统不提供自动诊疗建议。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="data" class="metric-grid">
      <div class="metric">
        <strong>{{ data.activePlans }}</strong>
        <span>活跃计划</span>
      </div>
      <div class="metric">
        <strong>{{ data.patientCount }}</strong>
        <span>负责患者</span>
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
      <section v-if="data" class="card">
        <div class="section-title">
          <div>
            <p class="eyebrow">Patient queue</p>
            <h2>患者协同队列</h2>
          </div>
          <span class="muted">{{ data.patients.length }} 人</span>
        </div>

        <div class="patient-list">
          <article
            v-for="row in data.patients"
            :key="row.planId"
            class="patient-row"
          >
            <div class="patient-avatar">{{ row.patient.displayName.slice(0, 1) }}</div>
            <div class="patient-main">
              <strong>{{ row.patient.displayName }}</strong>
              <p>{{ row.patient.recordNumber }} · {{ row.planStatus }}</p>
            </div>
            <div class="patient-stats">
              <span :class="{ warn: row.openTasks > 0 }">{{ row.openTasks }} 待办</span>
              <span :class="{ danger: row.openAlerts > 0 }">{{ row.openAlerts }} 提醒</span>
            </div>
            <el-button
              plain
              type="primary"
              size="small"
              @click="openCreate(row.patient.id, row.patient.displayName)"
            >
              新计划
            </el-button>
          </article>
        </div>
        <div v-if="!data.patients.length" class="empty-state">当前没有负责患者。</div>
      </section>

      <section class="card">
        <p class="eyebrow">Plan templates</p>
        <h2>已发布模板</h2>
        <article v-for="template in templates" :key="template.id" class="template-row">
          <div>
            <strong>{{ template.name }}</strong>
            <p>{{ template.conditionFocus }} · V{{ template.version }}</p>
          </div>
          <el-tag type="success" effect="plain">已发布</el-tag>
        </article>
        <p class="template-note">
          模板发布后不可原地修改。患者计划的调整必须生成新版本，并保留医生签署记录。
        </p>
      </section>
    </div>

    <el-dialog v-model="dialogOpen" title="创建新版治疗计划" width="520px">
      <el-form label-position="top">
        <el-form-item label="计划名称">
          <el-input v-model="form.title" maxlength="160" />
        </el-form-item>
        <el-form-item label="治疗模板">
          <el-select v-model="form.templateId" style="width: 100%">
            <el-option
              v-for="template in templates"
              :key="template.id"
              :label="`${template.name} · V${template.version}`"
              :value="template.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="form.startDate"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <p class="dialog-note">
        创建后将生成任务、用药安排与患者确认项。示例药物与阈值不对应真实临床指南。
      </p>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="!form.patientId || !form.templateId || !form.title"
          @click="createPlan"
        >
          创建并提交患者确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.section-title {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.section-title h2 {
  margin: 4px 0 0;
}

.patient-list {
  margin-top: 16px;
}

.patient-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto auto;
  gap: 14px;
  align-items: center;
  padding: 14px 0;
  border-top: 1px solid #edf3f1;
}

.patient-row:first-child {
  border-top: 0;
}

.patient-avatar {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--cp-primary-soft);
  color: var(--cp-primary);
  font-weight: 800;
}

.patient-main p,
.template-row p {
  color: var(--cp-muted);
  margin: 4px 0 0;
  font-size: 12px;
}

.patient-stats {
  display: flex;
  gap: 8px;
}

.patient-stats span {
  border-radius: 999px;
  background: #f1f6f4;
  padding: 5px 9px;
  color: var(--cp-muted);
  font-size: 11px;
}

.patient-stats .warn {
  color: #8c5a1f;
  background: #fff3df;
}

.patient-stats .danger {
  color: var(--cp-danger);
  background: #fbecea;
}

.template-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 15px 0;
  border-top: 1px solid #edf3f1;
}

.template-row:nth-of-type(2) {
  border-top: 0;
}

.template-note,
.dialog-note {
  color: var(--cp-muted);
  background: #f7faf9;
  border-radius: 10px;
  padding: 11px 12px;
  font-size: 12px;
  line-height: 1.65;
}

@media (max-width: 700px) {
  .patient-row {
    grid-template-columns: 42px minmax(0, 1fr);
  }

  .patient-stats,
  .patient-row .el-button {
    grid-column: 2;
  }
}
</style>
