const app = getApp()

Page({
  data: {
    notifications: []
  },

  onLoad() {
    this.loadNotifications()
  },

  onShow() {
    this.loadNotifications()
  },

  async loadNotifications() {
    try {
      const res = await app.request('/notifications')
      this.setData({ notifications: res || [] })
    } catch (e) {
      console.error('加载通知失败', e)
    }
  },

  async markAsRead(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/notifications/${id}/read`, { method: 'POST' })
      this.loadNotifications()
    } catch (e) {
      console.error('标记已读失败', e)
    }
  }
})
