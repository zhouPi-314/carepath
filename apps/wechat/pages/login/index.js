const { request } = require("../../utils/api");

Page({
  data: {
    username: "patient",
    password: "Pa2026!care",
    loading: false,
    error: "",
    accounts: [
      { username: "patient", label: "患者", password: "Pa2026!care" },
      { username: "caregiver", label: "家属", password: "Ca2026!care" },
    ],
  },

  onLoad() {
    if (wx.getStorageSync("carepath.accessToken")) {
      const session = wx.getStorageSync("carepath.session");
      const isUser = session && (session.role === "PATIENT" || session.role === "CAREGIVER");
      wx.reLaunch({ url: isUser ? "/pages/home/index" : "/pages/manage/index" });
    }
  },

  chooseAccount(event) {
    const target = event.currentTarget.dataset.username;
    const account = this.data.accounts.find((item) => item.username === target);
    this.setData({
      username: target,
      password: account ? account.password : "Pa2026!care",
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
      const isUser = session.user.role === "PATIENT" || session.user.role === "CAREGIVER";
      wx.reLaunch({ url: isUser ? "/pages/home/index" : "/pages/manage/index" });
    } catch (error) {
      this.setData({ error: error.message || "登录失败" });
    } finally {
      this.setData({ loading: false });
    }
  },
});
