const { request } = require("../../utils/api");

Page({
  data: {
    summary: null,
    roleClass: "user",
    loading: true,
    error: "",
  },

  onLoad() {
    if (!wx.getStorageSync("carepath.accessToken")) {
      wx.reLaunch({ url: "/pages/login/index" });
      return;
    }
    this.load();
  },

  async load() {
    this.setData({ loading: true, error: "" });
    try {
      const summary = await request("/mobile/summary");
      this.setData({ summary, roleClass: (summary.role || "user").toLowerCase() });
    } catch (error) {
      this.setData({ error: error.message || "无法加载管理面板" });
    } finally {
      this.setData({ loading: false });
    }
  },

  logout() {
    wx.removeStorageSync("carepath.accessToken");
    wx.removeStorageSync("carepath.session");
    wx.reLaunch({ url: "/pages/login/index" });
  },
});
