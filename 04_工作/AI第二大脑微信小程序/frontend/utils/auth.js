const app = getApp()

module.exports = {
  checkSession: () => {
    return new Promise((resolve, reject) => {
      wx.checkSession({
        success: resolve,
        fail: reject
      })
    })
  },

  requireAuth: async () => {
    try {
      await module.exports.checkSession()
      if (!app.globalData.token) {
        await app.login()
      }
    } catch (e) {
      await app.login()
    }
  }
}