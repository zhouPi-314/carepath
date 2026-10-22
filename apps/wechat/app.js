App({
  globalData: {
    session: null,
    sandboxMode: true,
  },
  onLaunch() {
    const session = wx.getStorageSync("carepath.session");
    if (session) {
      this.globalData.session = session;
    }
  },
});
