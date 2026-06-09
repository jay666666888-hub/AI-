App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: "http://localhost:8000/api"
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  },

  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              const response = await this.request('/auth/wx-login', {
                method: 'POST',
                body: { code: res.code }
              })
              this.globalData.token = response.access_token
              this.globalData.userInfo = response.user
              wx.setStorageSync('token', response.access_token)
              resolve(response)
            } catch (e) {
              reject(e)
            }
          } else {
            reject(new Error('微信登录失败'))
          }
        }
      })
    })
  },

  request(url, options = {}) {
    return new Promise((resolve, reject) => {
      const { baseUrl, token } = this.globalData
      wx.request({
        url: `${baseUrl}${url}`,
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...options.header
        },
        ...options,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            this.login().then(resolve).catch(reject)
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  }
})