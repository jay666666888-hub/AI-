const app = getApp()

Page({
  data: {
    userInfo: null
  },

  onLoad() {
    this.setData({ userInfo: app.globalData.userInfo })
  },

  goToHabits() {
    wx.navigateTo({ url: '/pages/habits/index' })
  },

  goToTimeline() {
    wx.navigateTo({ url: '/pages/timeline/index' })
  },

  goToMemory() {
    wx.navigateTo({ url: '/pages/memory/index' })
  },

  goToNotifications() {
    wx.navigateTo({ url: '/pages/notifications/index' })
  },

  goToSettings() {
    wx.showToast({ title: '设置功能开发中', icon: 'none' })
  }
})
