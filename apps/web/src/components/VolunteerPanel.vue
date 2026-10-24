<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiRequest, explainApiError } from "../lib/api";

interface Metric {
  label: string;
  value: number;
}

interface Task {
  id: string;
  title: string;
  category: string;
  status: string;
  dueAt: string | null;
}

const summary = ref<{ heading: string; identityLabel: string; metrics: Metric[] } | null>(null);
const tasks = ref<Task[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [info, myTasks] = await Promise.all([
      apiRequest<{ heading: string; identityLabel: string; metrics: Metric[] }>("/mobile/summary"),
      apiRequest<Task[]>("/community/my-tasks"),
    ]);
    summary.value = info;
    tasks.value = myTasks;
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
      <p class="eyebrow">Volunteer workspace</p>
      <h1 class="page-heading">我的志愿任务</h1>
      <p class="page-subtitle">仅展示指派给本人的社区随访与药品配送任务。</p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="summary" class="metric-grid">
      <div v-for="metric in summary.metrics" :key="metric.label" class="metric">
        <strong>{{ metric.value }}</strong>
        <span>{{ metric.label }}</span>
      </div>
    </div>

    <section v-if="tasks.length" class="card">
      <h2>任务清单</h2>
      <ul class="plain-list">
        <li v-for="task in tasks" :key="task.id">
          <strong>{{ task.title }}</strong>
          <span>{{ task.category }} · {{ task.status }}</span>
        </li>
      </ul>
    </section>

    <section v-else-if="!loading" class="card">
      <p>暂无指派任务。</p>
    </section>
  </div>
</template>

<style scoped>
.plain-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.plain-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--cp-line);
  padding-bottom: 8px;
  font-size: 13px;
  color: var(--cp-muted);
}

.plain-list strong {
  color: var(--cp-ink);
}
</style>
