<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";
import { formatDateTime } from "../lib/format";
import type { OfficialDataset } from "../types";

const datasets = ref<OfficialDataset[]>([]);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const form = reactive({
  sourceCode: "NMPA",
  title: "",
  version: "",
  sourceUrl: "https://www.nmpa.gov.cn/",
  checksum: "",
  reviewer: "系统管理员",
  contentText: '{\n  "records": []\n}',
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    datasets.value = await apiRequest<OfficialDataset[]>("/admin/official-datasets");
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

async function importDataset() {
  saving.value = true;
  try {
    const content = JSON.parse(form.contentText) as Record<string, unknown>;
    await apiRequest("/admin/official-datasets", {
      method: "POST",
      body: JSON.stringify({
        sourceCode: form.sourceCode,
        title: form.title,
        version: form.version,
        sourceUrl: form.sourceUrl,
        checksum: form.checksum,
        reviewer: form.reviewer,
        content,
      }),
    });
    ElMessage.success("官方数据快照已导入并记录审计。");
    form.title = "";
    form.version = "";
    form.checksum = "";
    await load();
  } catch (caught) {
    ElMessage.error(
      caught instanceof SyntaxError ? "内容必须是合法 JSON。" : explainApiError(caught),
    );
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header>
      <p class="eyebrow">Official data governance</p>
      <h1 class="page-heading">官方数据管理</h1>
      <p class="page-subtitle">
        人工导入合法公开资料，记录来源、版本、校验和、审核人与生效期，不执行高频抓取。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div class="split-grid">
      <section class="card">
        <p class="eyebrow">Snapshot registry</p>
        <h2>已导入版本</h2>
        <article v-for="item in datasets" :key="item.id" class="dataset-card">
          <div>
            <div class="dataset-meta">
              <span>{{ item.sourceCode }}</span>
              <span>V{{ item.version }}</span>
            </div>
            <strong>{{ item.title }}</strong>
            <p>
              {{ item.reviewer }} · {{ formatDateTime(item.importedAt) }} ·
              {{ item.parserVersion }}
            </p>
            <code>{{ item.checksum }}</code>
          </div>
          <el-tag type="success" effect="plain">{{ item.status }}</el-tag>
        </article>
      </section>

      <section class="card">
        <p class="eyebrow">Manual import</p>
        <h2>新增官方快照</h2>
        <el-form label-position="top">
          <el-form-item label="来源代码">
            <el-select v-model="form.sourceCode" style="width: 100%">
              <el-option label="NMPA 药品" value="NMPA" />
              <el-option label="NHSA 医保" value="NHSA" />
              <el-option label="NHC 卫健" value="NHC" />
              <el-option label="NBS 统计" value="NBS" />
            </el-select>
          </el-form-item>
          <el-form-item label="快照名称">
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="版本">
            <el-input v-model="form.version" placeholder="2026-10" />
          </el-form-item>
          <el-form-item label="来源 URL">
            <el-input v-model="form.sourceUrl" />
          </el-form-item>
          <el-form-item label="SHA-256 或来源校验值">
            <el-input v-model="form.checksum" minlength="16" />
          </el-form-item>
          <el-form-item label="内容 JSON">
            <el-input v-model="form.contentText" type="textarea" :rows="6" />
          </el-form-item>
          <el-button
            type="primary"
            :loading="saving"
            :disabled="!form.title || !form.version || form.checksum.length < 16"
            style="width: 100%"
            @click="importDataset"
          >
            导入并登记
          </el-button>
        </el-form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dataset-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 15px 0;
  border-top: 1px solid #edf3f1;
}

.dataset-card:first-of-type {
  border-top: 0;
}

.dataset-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 7px;
}

.dataset-meta span {
  border-radius: 999px;
  background: var(--cp-primary-soft);
  color: var(--cp-primary);
  font-size: 10px;
  font-weight: 800;
  padding: 4px 8px;
}

.dataset-card p {
  color: var(--cp-muted);
  font-size: 12px;
  margin: 5px 0;
}

.dataset-card code {
  color: #496a6d;
  font-size: 11px;
  overflow-wrap: anywhere;
}
</style>
