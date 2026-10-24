const { request } = require("../../utils/api");

const ROLES = [
  { key: "hospital", title: "医院", desc: "医生与院务管理", icon: "🏥", accounts: [
    { username: "doctor", password: "Do2026!care", label: "医生" },
    { username: "hospital", password: "Ho2026!care", label: "院务" },
  ]},
  { key: "community", title: "社区与志愿", desc: "志愿调度与药品配送", icon: "🌿", accounts: [
    { username: "community", password: "Co2026!care", label: "社区协调" },
    { username: "volunteer", password: "Vo2026!care", label: "志愿者" },
  ]},
  { key: "pharma", title: "药企", desc: "药品供应与产能", icon: "💊", accounts: [
    { username: "pharma", password: "Ph2026!care", label: "药企计划员" },
  ]},
  { key: "government", title: "政府", desc: "入驻认证与区域监管", icon: "🛡️", accounts: [
    { username: "regulator", password: "Re2026!care", label: "监管审核员" },
  ]},
  { key: "user", title: "用户 / 居民", desc: "病患与家属统一入口", icon: "🌱", accounts: [
    { username: "patient", password: "Pa2026!care", label: "居民" },
  ]},
];

Page({
  data: { roles: ROLES, activeRole: 0, activeAccount: 0, username: "doctor", password: "Do2026!care", loading: false, error: "" },
  onLoad() {
    if (wx.getStorageSync("carepath.accessToken")) {
      const session = wx.getStorageSync("carepath.session");
      const isUser = session && (session.role === "PATIENT" || session.role === "CAREGIVER");
      wx.reLaunch({ url: isUser ? "/pages/home/index" : "/pages/manage/index" });
    }
  },
  onRoleChange(event) {
    const index = event.detail.current;
    this.setData({ activeRole: index, activeAccount: 0, error: "" });
    this.applyAccount(index, 0);
  },
  chooseAccount(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.setData({ activeAccount: index, error: "" });
    this.applyAccount(this.data.activeRole, index);
  },
  applyAccount(roleIndex, accountIndex) {
    const account = ROLES[roleIndex].accounts[accountIndex];
    this.setData({ username: account.username, password: account.password });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  async submit() {
    if (this.data.loading) return;
    this.setData({ loading: true, error: "" });
    try {
      const session = await request("/auth/login", { method: "POST", data: { username: this.data.username.trim(), password: this.data.password } });
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
