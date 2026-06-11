const app = getApp()

Page({
  data: {
    habits: [],
    stats: null
  },

  onLoad() {
    this.loadHabits()
  },

  onShow() {
    this.loadHabits()
  },

  async loadHabits() {
    try {
      const res = await app.request('/tasks/habits/today')
      this.setData({ 
        habits: res.habits || [],
        stats: res
      })
    } catch (e) {
      console.error('加载习惯失败', e)
    }
  },

  async logHabit(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/tasks/habits/${id}/log`, {
        method: 'POST',
        body: { status: 'completed' }
      })
      wx.showToast({ title: '打卡成功', icon: 'success' })
      this.loadHabits()
    } catch (e) {
      wx.showToast({ title: '打卡失败', icon: 'none' })
    }
  }
})
