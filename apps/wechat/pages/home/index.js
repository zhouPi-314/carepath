const { request } = require("../../utils/api");
const {
  completionRate,
  taskStateLabel,
  formatDateTime,
} = require("../../utils/presentation");

Page({
  data: {
    dashboard: null,
    session: {},
    planTitle: "",
    summary: "按计划完成随访并记录变化。",
    tasks: [],
    nextTask: null,
    progress: 0,
    openAlertCount: 0,
    loading: true,
    error: "",
    offlineWarning: "",
  },

  onLoad() {
    const session = wx.getStorageSync("carepath.session");
    if (!wx.getStorageSync("carepath.accessToken") || !session) {
      wx.reLaunch({ url: "/pages/login/index" });
      return;
    }
    this.setData({ session });
    this.loadDashboard();
  },

  async onPullDownRefresh() {
    await this.loadDashboard();
    wx.stopPullDownRefresh();
  },

  async loadDashboard() {
    this.setData({ loading: true, error: "", offlineWarning: "" });
    try {
      const dashboard = await request("/patient/dashboard");
      wx.setStorageSync("carepath.dashboard", dashboard);
      this.applyDashboard(dashboard);
    } catch (error) {
      const cached = wx.getStorageSync("carepath.dashboard");
      if (cached) {
        this.applyDashboard(cached);
        this.setData({ offlineWarning: "后端暂不可用，当前显示本地缓存。" });
      } else {
        this.setData({ error: error.message || "无法加载治疗进度" });
      }
    } finally {
      this.setData({ loading: false });
    }
  },

  applyDashboard(dashboard) {
    const tasks = dashboard.tasks.map((task) => ({
      ...task,
      dueLabel: formatDateTime(task.dueAt),
      stateLabel: taskStateLabel(task),
      stateClass:
        task.status === "COMPLETED"
          ? "done"
          : task.isOverdue
            ? "overdue"
            : "pending",
    }));
    this.setData({
      dashboard,
      tasks,
      nextTask: tasks.find((task) => task.status !== "COMPLETED") || null,
      progress: completionRate(tasks),
      openAlertCount: dashboard.alerts.filter((alert) => alert.status === "OPEN").length,
      planTitle: dashboard.plan ? dashboard.plan.title : "暂无已发布计划",
      summary:
        (dashboard.plan &&
          dashboard.plan.content &&
          dashboard.plan.content.summary) ||
        "按计划完成随访并记录变化。",
    });
  },

  async completeTask(event) {
    const taskId = event.currentTarget.dataset.id;
    wx.showLoading({ title: "同步中" });
    try {
      await request(`/tasks/${taskId}/complete`, {
        method: "POST",
        data: { note: "微信小程序确认完成" },
      });
      wx.showToast({ title: "任务已同步", icon: "success" });
      await this.loadDashboard();
    } catch (error) {
      wx.showToast({
        title: error.message || "同步失败",
        icon: "none",
      });
    } finally {
      wx.hideLoading();
    }
  },

  logout() {
    wx.removeStorageSync("carepath.accessToken");
    wx.removeStorageSync("carepath.session");
    wx.removeStorageSync("carepath.dashboard");
    getApp().globalData.session = null;
    wx.reLaunch({ url: "/pages/login/index" });
  },
});
