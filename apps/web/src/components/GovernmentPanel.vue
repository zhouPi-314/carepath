<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";
import { alertStatusLabels, formatDateTime, formatPercent } from "../lib/format";
import type {
  GovernmentMetricsData,
  OfficialDataset,
  ReviewCase,
} from "../types";
import MetricsChart from "./MetricsChart.vue";

const metrics = ref<GovernmentMetricsData | null>(null);
const reviews = ref<ReviewCase[]>([]);
const datasets = ref<OfficialDataset[]>([]);
const loading = ref(true);
const reviewing = ref<string | null>(null);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [metrics.value, reviews.value, datasets.value] = await Promise.all([
      apiRequest<GovernmentMetricsData>("/government/metrics"),
      apiRequest<ReviewCase[]>("/government/reviews"),
      apiRequest<OfficialDataset[]>("/admin/official-datasets"),
    ]);
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

async function decide(caseId: string, approved: boolean) {
  reviewing.value = caseId;
  try {
    await apiRequest(`/government/reviews/${caseId}/decision`, {
      method: "POST",
      body: JSON.stringify({
        approved,
        note: approved ? "平台内演示审核通过" : "演示审核驳回，等待材料补充",
      }),
    });
    ElMessage.success(approved ? "审核已通过并写入审计。" : "已记录驳回意见。");
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  } finally {
    reviewing.value = null;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header>
      <p class="eyebrow">De-identified oversight</p>
      <h1 class="page-heading">区域监管沙箱</h1>
      <p class="page-subtitle">
        仅展示区域级聚合指标和平台内审核案件，不包含患者、医生或医院级诊疗明细。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="metrics" class="metric-grid">
      <div class="metric">
        <strong>{{ metrics.regions.length }}</strong>
        <span>已统计区域</span>
      </div>
      <div class="metric">
        <strong>{{ metrics.minimumCellSize }}</strong>
        <span>最小发布单元</span>
      </div>
      <div class="metric">
        <strong>{{ reviews.filter((item) => item.status === "PENDING").length }}</strong>
        <span>待审核案件</span>
      </div>
      <div class="metric">
        <strong>{{ datasets.length }}</strong>
        <span>官方数据快照</span>
      </div>
    </div>

    <div class="split-grid">
      <section class="card">
        <div class="section-title">
          <div>
            <p class="eyebrow">Regional view</p>
            <h2>区域活跃计划</h2>
          </div>
          <span class="muted">最小人数抑制已启用</span>
        </div>
        <MetricsChart v-if="metrics" :rows="metrics.regions" />
        <div class="region-table">
          <div class="region-head">
            <span>区域</span><span>活跃计划</span><span>任务完成率</span><span>待处理提醒</span>
          </div>
          <div v-for="row in metrics?.regions" :key="row.regionCode" class="region-row">
            <strong>{{ row.regionCode }}</strong>
            <span>{{ row.activePlans ?? "已抑制" }}</span>
            <span>{{ formatPercent(row.taskCompletionRate) }}</span>
            <span>{{ row.openAlerts ?? "已抑制" }}</span>
          </div>
        </div>
        <ul class="disclaimer-list">
          <li v-for="item in metrics?.disclaimers" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="card">
        <p class="eyebrow">Verification queue</p>
        <h2>平台内审核</h2>
        <article v-for="item in reviews" :key="item.id" class="review-card">
          <div>
            <strong>{{ item.subject }}</strong>
            <p>{{ item.type }} · {{ formatDateTime(item.createdAt) }}</p>
          </div>
          <el-tag
            :type="item.status === 'PENDING' ? 'warning' : item.status === 'APPROVED' ? 'success' : 'danger'"
            effect="plain"
          >
            {{ alertStatusLabels[item.status] ?? item.status }}
          </el-tag>
          <div v-if="item.status === 'PENDING'" class="review-actions">
            <el-button
              size="small"
              :loading="reviewing === item.id"
              @click="decide(item.id, false)"
            >
              驳回
            </el-button>
            <el-button
              type="primary"
              size="small"
              :loading="reviewing === item.id"
              @click="decide(item.id, true)"
            >
              通过
            </el-button>
          </div>
        </article>
      </section>
    </div>

    <section class="card">
      <div class="section-title">
        <div>
          <p class="eyebrow">Official snapshots</p>
          <h2>数据来源与版本</h2>
        </div>
        <span class="muted">人工导入 · 校验和可追踪</span>
      </div>
      <el-table :data="datasets" class="dataset-table">
        <el-table-column prop="sourceCode" label="来源" width="100" />
        <el-table-column prop="title" label="快照" min-width="280" />
        <el-table-column prop="version" label="版本" min-width="160" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="校验和" min-width="190">
          <template #default="{ row }">
            <code>{{ row.checksum.slice(0, 18) }}…</code>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.section-title {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.section-title h2 {
  margin: 4px 0 8px;
}

.region-table {
  border-top: 1px solid #edf3f1;
  margin-top: 8px;
}

.region-head,
.region-row {
  display: grid;
  grid-template-columns: 1.1fr repeat(3, 1fr);
  gap: 10px;
  align-items: center;
  min-height: 44px;
  border-bottom: 1px solid #edf3f1;
  font-size: 13px;
}

.region-head {
  color: var(--cp-muted);
  font-size: 11px;
  font-weight: 700;
}

.disclaimer-list {
  color: var(--cp-muted);
  font-size: 12px;
  line-height: 1.65;
  padding-left: 18px;
}

.review-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding: 14px 0;
  border-top: 1px solid #edf3f1;
}

.review-card:first-of-type {
  border-top: 0;
}

.review-card p {
  color: var(--cp-muted);
  margin: 4px 0;
  font-size: 12px;
}

.review-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.dataset-table {
  margin-top: 14px;
  --el-table-border-color: #e3ece9;
  --el-table-header-bg-color: #f5f9f8;
}

code {
  color: #335d60;
  font-size: 11px;
}
</style>
