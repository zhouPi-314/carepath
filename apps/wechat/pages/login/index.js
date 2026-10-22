const { request } = require("../../utils/api");

Page({
  data: {
    username: "patient",
    password: "CarePath123!",
    loading: false,
    error: "",
    accounts: [
      { username: "patient", label: "患者" },
      { username: "caregiver", label: "家属" },
    ],
  },

  onLoad() {
    if (wx.getStorageSync("carepath.accessToken")) {
      wx.reLaunch({ url: "/pages/home/index" });
    }
  },

  chooseAccount(event) {
    this.setData({
      username: event.currentTarget.dataset.username,
      password: "CarePath123!",
      error: "",
    });
  },

  onInput(event) {
    this.setData({
      [event.currentTarget.dataset.field]: event.detail.value,
    });
  },

  async submit() {
    if (this.data.loading) return;
    this.setData({ loading: true, error: "" });
    try {
      const session = await request("/auth/login", {
        method: "POST",
        data: {
          username: this.data.username.trim(),
          password: this.data.password,
        },
      });
      wx.setStorageSync("carepath.accessToken", session.accessToken);
      wx.setStorageSync("carepath.session", session.user);
      getApp().globalData.session = session.user;
      wx.reLaunch({ url: "/pages/home/index" });
    } catch (error) {
      this.setData({ error: error.message || "登录失败" });
    } finally {
      this.setData({ loading: false });
    }
  },
});
