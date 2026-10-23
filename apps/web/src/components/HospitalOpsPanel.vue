<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest, explainApiError } from "../lib/api";

interface Staff {
  id: string;
  username: string;
  displayName: string;
  role: string;
  active: boolean;
}

interface Transfer {
  id: string;
  patientId: string;
  toOrganizationId: string;
  level: string;
  status: string;
  reason: string;
}

interface RecordItem {
  id: string;
  title: string;
  recordType: string;
  visibility: string;
  content: { summary?: string };
  createdAt: string;
}

const staff = ref<Staff[]>([]);
const transfers = ref<Transfer[]>([]);
const records = ref<RecordItem[]>([]);
const error = ref("");

const staffForm = ref({ username: "", displayName: "", password: "Care2026!staff" });
const transferForm = ref({ toOrganizationId: "org-community", level: "COMMUNITY", reason: "" });
const recordForm = ref({ title: "", summary: "", visibility: "CARE_TEAM_AND_FAMILY" });

async function load() {
  error.value = "";
  try {
    [staff.value, transfers.value, records.value] = await Promise.all([
      apiRequest<Staff[]>("/hospital/staff"),
      apiRequest<Transfer[]>("/hospital/transfers"),
      apiRequest<RecordItem[]>("/hospital/treatment-records/patient-main"),
    ]);
  } catch (caught) {
    error.value = explainApiError(caught);
  }
}

async function createStaff() {
  try {
    await apiRequest("/hospital/staff", {
      method: "POST",
      body: JSON.stringify({
        username: staffForm.value.username,
        displayName: staffForm.value.displayName,
        password: staffForm.value.password,
        role: "DOCTOR",
      }),
    });
    ElMessage.success("职工已录入");
    staffForm.value.username = "";
    staffForm.value.displayName = "";
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  }
}

async function createTransfer() {
  try {
    await apiRequest("/hospital/transfers", {
      method: "POST",
      body: JSON.stringify({
        patientId: "patient-main",
        toOrganizationId: transferForm.value.toOrganizationId,
        level: transferForm.value.level,
        reason: transferForm.value.reason,
      }),
    });
    ElMessage.success("转诊已登记");
    transferForm.value.reason = "";
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  }
}

async function createRecord() {
  if (!recordForm.value.title.trim()) return;
  try {
    await apiRequest("/hospital/treatment-records", {
      method: "POST",
      body: JSON.stringify({
        planId: "plan-main",
        recordType: "PROGRESS",
        title: recordForm.value.title,
        summary: recordForm.value.summary,
        visibility: recordForm.value.visibility,
      }),
    });
    ElMessage.success("治疗记录已写入");
    recordForm.value.title = "";
    recordForm.value.summary = "";
    await load();
  } catch (caught) {
    ElMessage.error(explainApiError(caught));
  }
}

onMounted(load);
</script>

<template>
  <section class="panel-stack">
    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />

    <section class="card">
      <h2>医院职工</h2>
      <ul class="plain-list">
        <li v-for="member in staff" :key="member.id">
          <strong>{{ member.displayName }}</strong>
          <span>{{ member.role }} · {{ member.username }} · {{ member.active ? "在岗" : "停用" }}</span>
        </li>
      </ul>
      <div class="inline-form">
        <el-input v-model="staffForm.username" placeholder="登录账号" />
        <el-input v-model="staffForm.displayName" placeholder="姓名" />
        <el-input v-model="staffForm.password" placeholder="初始密码" />
        <el-button type="primary" @click="createStaff">录入医生</el-button>
      </div>
    </section>

    <section class="card">
      <h2>分级转入</h2>
      <ul class="plain-list">
        <li v-for="item in transfers" :key="item.id">
          <strong>{{ item.patientId }}</strong>
          <span>{{ item.level }} → {{ item.toOrganizationId }} · {{ item.status }} · {{ item.reason }}</span>
        </li>
      </ul>
      <div class="inline-form">
        <el-select v-model="transferForm.toOrganizationId" style="width: 200px">
          <el-option label="社区照护中心" value="org-community" />
          <el-option label="康复医院" value="org-hospital-b" />
        </el-select>
        <el-input v-model="transferForm.reason" placeholder="转入原因" />
        <el-button type="primary" @click="createTransfer">登记转入</el-button>
      </div>
    </section>

    <section class="card">
      <h2>治疗记录</h2>
      <ul class="plain-list">
        <li v-for="item in records" :key="item.id">
          <strong>{{ item.title }}</strong>
          <span>{{ item.recordType }} · {{ item.visibility }} · {{ item.content.summary }}</span>
        </li>
      </ul>
      <div class="inline-form">
        <el-input v-model="recordForm.title" placeholder="记录标题" />
        <el-input v-model="recordForm.summary" placeholder="进展摘要" />
        <el-button type="primary" @click="createRecord">写入记录</el-button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.inline-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.plain-list {
  list-style: none;
  margin: 0 0 8px;
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
