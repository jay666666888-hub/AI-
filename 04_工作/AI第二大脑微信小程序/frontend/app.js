const API_CONFIG = require('./services2/config.js')

App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: API_CONFIG.baseUrl,
    loginPromise: null  // 保存登录Promise，确保所有登录调用等待同一个登录完成
  },

  onLaunch() {
    // 强制清除旧token，避免后端重启后token失效导致403
    wx.removeStorageSync('token')
    this.globalData.token = null
    // 触发登录
    this.login()
  },

  login() {
    // 如果已有登录在进行中，返回同一个Promise等待完成
    if (this.loginPromise) {
      return this.loginPromise
    }

    this.loginPromise = new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              const response = await this._rawRequest('/auth/wx-login', {
                method: 'POST',
                body: { code: res.code }
              })
              this.globalData.token = response.access_token
              this.globalData.userInfo = response.user
              wx.setStorageSync('token', response.access_token)
              this.loginPromise = null  // 登录完成后清除
              resolve(response)
            } catch (e) {
              this.loginPromise = null
              reject(e)
            }
          } else {
            this.loginPromise = null
            reject(new Error('微信登录失败'))
          }
        },
        fail: (err) => {
          this.loginPromise = null
          reject(err)
        }
      })
    })
    return this.loginPromise
  },

  // 直接发送请求，不排队
  _rawRequest(url, options = {}) {
    const { baseUrl, token } = this.globalData
    return new Promise((resolve, reject) => {
      const headers = {
        'Content-Type': 'application/json',
        ...options.header
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      wx.request({
        url: `${baseUrl}${url}`,
        header: headers,
        method: options.method || 'GET',
        data: options.body,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            // Token无效，重新登录
            this.login().then(() => {
              this._rawRequest(url, options).then(resolve).catch(reject)
            }).catch(reject)
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  },

  request(url, options = {}) {
    const { token } = this.globalData

    // 如果没有token，先登录
    if (!token) {
      return this.login().then(() => this._rawRequest(url, options))
    }

    return this._rawRequest(url, options)
  }
})