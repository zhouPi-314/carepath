<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";
import { formatDateTime } from "../lib/format";
import type { PharmaDashboardData } from "../types";

const data = ref<PharmaDashboardData | null>(null);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const report = reactive({
  productId: "",
  regionCode: "310000",
  period: new Date().toISOString().slice(0, 7),
  capacityUnits: 100000,
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await apiRequest<PharmaDashboardData>("/pharma/dashboard");
    report.productId = data.value.products[0]?.id ?? "";
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

async function submitCapacity() {
  saving.value = true;
  try {
    await apiRequest("/pharma/capacity", {
      method: "POST",
      body: JSON.stringify(report),
    });
    ElMessage.success("产能反馈已写入平台，并记录审计事件。");
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
      <p class="eyebrow">Aggregated supply signal</p>
      <h1 class="page-heading">药品需求与产能</h1>
      <p class="page-subtitle">
        查看达到发布阈值的区域需求信号，并反馈产能。页面不展示患者、医生或医院明细。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="data" class="metric-grid">
      <div class="metric">
        <strong>{{ data.products.length }}</strong>
        <span>已登记药品</span>
      </div>
      <div class="metric">
        <strong>{{ data.demandSignals.length }}</strong>
        <span>可发布需求信号</span>
      </div>
      <div class="metric">
        <strong>{{ data.capacityReports.length }}</strong>
        <span>产能反馈</span>
      </div>
      <div class="metric">
        <strong>{{ data.products.filter((item) => item.verificationStatus === "VERIFIED").length }}</strong>
        <span>官方目录已匹配</span>
      </div>
    </div>

    <div class="split-grid">
      <section class="card">
        <p class="eyebrow">Demand signals</p>
        <h2>区域月度信号</h2>
        <article
          v-for="signal in data?.demandSignals"
          :key="`${signal.regionCode}-${signal.drugName}-${signal.period}`"
          class="signal-card"
        >
          <div class="signal-period">{{ signal.period }}</div>
          <div>
            <strong>{{ signal.drugName }}</strong>
            <p>{{ signal.regionCode }} · {{ signal.organizationCount }} 家机构</p>
          </div>
          <div class="signal-value">
            <strong>{{ signal.patientMonths }}</strong>
            <span>患者月</span>
          </div>
        </article>
        <p v-if="!data?.demandSignals.length" class="empty-state">
          当前没有达到“至少 3 家机构、50 个患者月”的发布条件。
        </p>
        <ul class="disclaimer-list">
          <li v-for="item in data?.disclaimers" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="card">
        <p class="eyebrow">Capacity feedback</p>
        <h2>提交产能反馈</h2>
        <el-form label-position="top">
          <el-form-item label="药品">
            <el-select v-model="report.productId" style="width: 100%">
              <el-option
                v-for="product in data?.products"
                :key="product.id"
                :label="product.name"
                :value="product.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="区域编码">
            <el-input v-model="report.regionCode" />
          </el-form-item>
          <el-form-item label="月份">
            <el-input v-model="report.period" placeholder="YYYY-MM" />
          </el-form-item>
          <el-form-item label="可供数量">
            <el-input-number v-model="report.capacityUnits" :min="0" style="width: 100%" />
          </el-form-item>
          <el-button
            type="primary"
            :loading="saving"
            :disabled="!report.productId"
            style="width: 100%"
            @click="submitCapacity"
          >
            保存反馈
          </el-button>
        </el-form>
      </section>
    </div>

    <div class="split-grid">
      <section class="card">
        <p class="eyebrow">Product registry</p>
        <h2>药品目录</h2>
        <article v-for="product in data?.products" :key="product.id" class="product-row">
          <div>
            <strong>{{ product.name }}</strong>
            <p>{{ product.manufacturer }} · {{ product.approvalNumber }}</p>
          </div>
          <el-tag type="success" effect="plain">{{ product.verificationStatus }}</el-tag>
        </article>
      </section>

      <section class="card">
        <p class="eyebrow">Submission history</p>
        <h2>反馈记录</h2>
        <article v-for="item in data?.capacityReports" :key="item.id" class="history-row">
          <div>
            <strong>{{ item.period }} · {{ item.regionCode }}</strong>
            <p>{{ item.capacityUnits.toLocaleString("zh-CN") }} 单位</p>
          </div>
          <span>{{ item.status }} · {{ formatDateTime(item.createdAt) }}</span>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.signal-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid #edf3f1;
}

.signal-card:first-of-type {
  border-top: 0;
}

.signal-period {
  width: 70px;
  border-radius: 10px;
  background: var(--cp-primary-soft);
  color: var(--cp-primary);
  padding: 8px 5px;
  text-align: center;
  font-size: 11px;
  font-weight: 800;
}

.signal-card p,
.product-row p,
.history-row p {
  color: var(--cp-muted);
  margin: 4px 0 0;
  font-size: 12px;
}

.signal-value {
  text-align: right;
}

.signal-value strong {
  display: block;
  font-size: 24px;
}

.signal-value span {
  color: var(--cp-muted);
  font-size: 11px;
}

.disclaimer-list {
  color: var(--cp-muted);
  font-size: 12px;
  line-height: 1.65;
}

.product-row,
.history-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid #edf3f1;
}

.product-row:first-of-type,
.history-row:first-of-type {
  border-top: 0;
}

.history-row > span {
  color: var(--cp-muted);
  font-size: 11px;
}
</style>
