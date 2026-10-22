const { API_BASE_URL } = require("../config");

function request(path, options) {
  const settings = options || {};
  const token = wx.getStorageSync("carepath.accessToken");
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${path}`,
      method: settings.method || "GET",
      data: settings.data,
      timeout: 15000,
      header: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data);
          return;
        }
        reject(
          new Error(
            (response.data && (response.data.detail || response.data.message)) ||
              `请求失败（${response.statusCode}）`,
          ),
        );
      },
      fail(error) {
        reject(new Error(error.errMsg || "无法连接后端服务"));
      },
    });
  });
}

module.exports = { request };
