<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";

interface Volunteer {
  id: string;
  name: string;
  phoneMasked: string;
  skills: string[];
  status: string;
}

interface Task {
  id: string;
  title: string;
  category: string;
  status: string;
  assigneeId: string | null;
}

interface Delivery {
  id: string;
  status: string;
  addressRegion: string;
  note: string;
}

interface Dashboard {
  organizationId: string;
  volunteerCount: number;
  openTaskCount: number;
  pendingDeliveryCount: number;
  volunteers: Volunteer[];
  tasks: Task[];
  deliveries: Delivery[];
}

const data = ref<Dashboard | null>(null);
const loading = ref(true);
const error = ref("");
const taskTitle = ref("");
const taskCategory = ref("VISIT");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await apiRequest<Dashboard>("/community/dashboard");
  } catch (caught) {
    error.value = explainApiError(caught);
  } finally {
    loading.value = false;
  }
}

async function createTask() {
  if (!taskTitle.value.trim()) return;
  try {
    await apiRequest("/community/tasks", {
      method: "POST",
      body: JSON.stringify({ title: taskTitle.value, category: taskCategory.value }),
    });
    taskTitle.value = "";
    ElMessage.success("社区任务已创建");
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  }
}

onMounted(load);
</script>

<template>
  <div class="panel-stack" v-loading="loading">
    <header>
      <p class="eyebrow">Community & volunteer operations</p>
      <h1 class="page-heading">社区照护与志愿调度</h1>
      <p class="page-subtitle">
        管理志愿者、社区随访任务与药品配送；所有数据限定在本组织范围内。
      </p>
    </header>

    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <div v-if="data" class="metric-grid">
      <div class="metric"><strong>{{ data.volunteerCount }}</strong><span>志愿者</span></div>
      <div class="metric"><strong>{{ data.openTaskCount }}</strong><span>待办任务</span></div>
      <div class="metric"><strong>{{ data.pendingDeliveryCount }}</strong><span>待配送</span></div>
    </div>

    <section v-if="data" class="card">
      <h2>新建社区任务</h2>
      <div class="inline-form">
        <el-input v-model="taskTitle" placeholder="任务标题，如：上门血压测量" />
        <el-select v-model="taskCategory" style="width: 140px">
          <el-option label="上门随访" value="VISIT" />
          <el-option label="药品配送" value="DELIVERY" />
          <el-option label="生活支持" value="SUPPORT" />
        </el-select>
        <el-button type="primary" @click="createTask">创建任务</el-button>
      </div>
    </section>

    <section v-if="data" class="card">
      <h2>志愿者</h2>
      <ul class="plain-list">
        <li v-for="volunteer in data.volunteers" :key="volunteer.id">
          <strong>{{ volunteer.name }}</strong>
          <span>{{ volunteer.phoneMasked }} · {{ volunteer.skills.join(" / ") || "通用" }}</span>
        </li>
      </ul>
    </section>

    <section v-if="data" class="card">
      <h2>社区任务</h2>
      <ul class="plain-list">
        <li v-for="task in data.tasks" :key="task.id">
          <strong>{{ task.title }}</strong>
          <span>{{ task.category }} · {{ task.status }} · 志愿者：{{ task.assigneeId || "待分配" }}</span>
        </li>
      </ul>
    </section>

    <section v-if="data" class="card">
      <h2>药品配送</h2>
      <ul class="plain-list">
        <li v-for="order in data.deliveries" :key="order.id">
          <strong>{{ order.addressRegion || "区域待补充" }}</strong>
          <span>{{ order.status }} · {{ order.note || "无备注" }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.inline-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

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
