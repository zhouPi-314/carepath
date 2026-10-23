const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const storage = new Map();
let relaunched = null;
let toasts = [];
let requestHandler = null;

global.wx = {
  getStorageSync(key) {
    return storage.has(key) ? storage.get(key) : "";
  },
  setStorageSync(key, value) {
    storage.set(key, value);
  },
  removeStorageSync(key) {
    storage.delete(key);
  },
  request(options) {
    requestHandler(options);
  },
  showLoading() {},
  hideLoading() {},
  showToast(payload) {
    toasts.push(payload);
  },
  stopPullDownRefresh() {},
  reLaunch({ url }) {
    relaunched = url;
  },
};

global.getApp = () => ({ globalData: { session: null } });

function reset() {
  storage.clear();
  relaunched = null;
  toasts = [];
  requestHandler = null;
}

function loadPage(relativePath) {
  let definition = null;
  const previousPage = global.Page;
  global.Page = (config) => {
    definition = config;
  };
  const resolved = require.resolve(path.join(__dirname, "..", relativePath));
  delete require.cache[resolved];
  require(resolved);
  global.Page = previousPage;
  assert.ok(definition, "page definition should be registered");
  return definition;
}

function instantiate(definition) {
  const page = Object.create(definition);
  page.data = JSON.parse(JSON.stringify(definition.data || {}));
  page.setData = function setData(patch) {
    Object.assign(this.data, patch);
  };
  return page;
}

function respondWith(data) {
  requestHandler = (options) => options.success({ statusCode: 200, data });
}

function failWith(message) {
  requestHandler = (options) => options.fail({ errMsg: message });
}

const dashboard = {
  patient: { displayName: "陈安" },
  plan: { title: "高血压计划", content: { summary: "演示摘要" } },
  tasks: [
    {
      id: "task-1",
      title: "血压记录",
      status: "PENDING",
      isOverdue: true,
      dueAt: "2026-10-22T08:00:00Z",
    },
    {
      id: "task-2",
      title: "用药核对",
      status: "COMPLETED",
      isOverdue: false,
      dueAt: "2026-10-21T08:00:00Z",
    },
  ],
  alerts: [{ id: "a1", status: "OPEN" }, { id: "a2", status: "RESOLVED" }],
  medications: [],
  caregivers: [],
};

test("login stores sandbox session and opens home", async () => {
  reset();
  respondWith({
    accessToken: "token-1",
    user: { displayName: "陈安" },
  });
  const page = instantiate(loadPage("pages/login/index.js"));

  await page.submit();

  assert.equal(storage.get("carepath.accessToken"), "token-1");
  assert.deepEqual(storage.get("carepath.session"), { displayName: "陈安" });
  assert.equal(relaunched, "/pages/home/index");
  assert.equal(page.data.loading, false);
});

test("login surfaces backend error without storing a session", async () => {
  reset();
  failWith("无法连接后端服务");
  const page = instantiate(loadPage("pages/login/index.js"));

  await page.submit();

  assert.equal(page.data.error, "无法连接后端服务");
  assert.equal(storage.has("carepath.accessToken"), false);
  assert.equal(relaunched, null);
});

test("home caches the dashboard and maps task state", async () => {
  reset();
  storage.set("carepath.accessToken", "token-1");
  storage.set("carepath.session", { displayName: "陈安" });
  respondWith(dashboard);
  const page = instantiate(loadPage("pages/home/index.js"));

  await page.loadDashboard();

  assert.equal(page.data.planTitle, "高血压计划");
  assert.equal(page.data.progress, 50);
  assert.equal(page.data.openAlertCount, 1);
  assert.equal(page.data.tasks[0].stateLabel, "已逾期");
  assert.equal(page.data.nextTask.id, "task-1");
  assert.equal(storage.get("carepath.dashboard"), dashboard);
  assert.equal(page.data.offlineWarning, "");
});

test("home falls back to cache when the backend is unavailable", async () => {
  reset();
  storage.set("carepath.dashboard", dashboard);
  failWith("request:fail timeout");
  const page = instantiate(loadPage("pages/home/index.js"));

  await page.loadDashboard();

  assert.equal(page.data.offlineWarning, "后端暂不可用，当前显示本地缓存。");
  assert.equal(page.data.planTitle, "高血压计划");
  assert.equal(page.data.loading, false);
});

test("home reports an error when the backend fails and no cache exists", async () => {
  reset();
  failWith("request:fail timeout");
  const page = instantiate(loadPage("pages/home/index.js"));

  await page.loadDashboard();

  assert.equal(page.data.error, "request:fail timeout");
  assert.equal(page.data.loading, false);
});

test("completing a task posts once and reloads the dashboard", async () => {
  reset();
  const calls = [];
  requestHandler = (options) => {
    calls.push({ url: options.url, method: options.method, data: options.data });
    if (options.url.endsWith("/complete")) {
      options.success({ statusCode: 200, data: { status: "COMPLETED" } });
    } else {
      options.success({ statusCode: 200, data: dashboard });
    }
  };
  const page = instantiate(loadPage("pages/home/index.js"));
  const { API_BASE_URL } = require("../config");

  await page.completeTask({ currentTarget: { dataset: { id: "task-1" } } });

  assert.equal(calls[0].url, API_BASE_URL + "/tasks/task-1/complete");
  assert.equal(calls[0].method, "POST");
  assert.equal(calls.length, 2);
  assert.equal(toasts[0].title, "任务已同步");
});

test("task completion failure keeps the view and reports the error", async () => {
  reset();
  failWith("无法连接后端服务");
  const page = instantiate(loadPage("pages/home/index.js"));

  await page.completeTask({ currentTarget: { dataset: { id: "task-1" } } });

  assert.equal(toasts[0].title, "无法连接后端服务");
});

test("logout clears sandbox credentials and returns to login", () => {
  reset();
  storage.set("carepath.accessToken", "token-1");
  storage.set("carepath.session", { displayName: "陈安" });
  storage.set("carepath.dashboard", dashboard);
  const page = instantiate(loadPage("pages/home/index.js"));

  page.logout();

  assert.equal(storage.has("carepath.accessToken"), false);
  assert.equal(storage.has("carepath.session"), false);
  assert.equal(storage.has("carepath.dashboard"), false);
  assert.equal(relaunched, "/pages/login/index");
});
