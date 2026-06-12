const app = getApp()

Page({
  data: {
    habits: [],
    stats: {
      date: '',
      total: 0,
      completed: 0,
      pending: 0,
      streak: 0
    },
    weekDays: []
  },

  onLoad() {
    this.initWeekDays()
    this.loadHabits()
  },

  onShow() {
    this.loadHabits()
  },

  initWeekDays() {
    const days = ['一', '二', '三', '四', '五', '六', '日']
    const today = new Date()
    const dayOfWeek = today.getDay() || 7
    const weekDays = []

    for (let i = 1; i <= 7; i++) {
      const diff = i - dayOfWeek
      const date = new Date(today)
      date.setDate(today.getDate() + diff)

      weekDays.push({
        day: days[i - 1],
        date: date.getDate(),
        completed: false, // Will be updated based on actual data
        today: i === dayOfWeek
      })
    }

    this.setData({ weekDays })
  },

  async loadHabits() {
    try {
      const res = await app.request('/tasks/habits/today')
      const stats = res || { habits: [], streak: 0 }

      // 更新统计数据
      const completed = (stats.habits || []).filter(h => h.is_completed_today).length
      const pending = (stats.habits || []).length - completed

      this.setData({
        habits: stats.habits || [],
        stats: {
          date: stats.date || new Date().toLocaleDateString('zh-CN'),
          total: stats.total || 0,
          completed,
          pending,
          streak: stats.streak || 0
        }
      })

      // 更新本周图表数据
      this.updateWeekChart(stats.habits || [])
    } catch (e) {
      console.error('加载习惯失败', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  updateWeekChart(habits) {
    // 这里需要根据实际打卡数据更新本周图表
    // 简化处理：假设今天之前的都完成了
    const weekDays = this.data.weekDays.map((day, index) => ({
      ...day,
      completed: day.today ? false : Math.random() > 0.3 // 临时模拟数据
    }))
    this.setData({ weekDays })
  },

  async logHabit(e) {
    const { id } = e.currentTarget.dataset
    try {
      wx.showLoading({ title: '打卡中...' })
      await app.request(`/tasks/habits/${id}/log`, {
        method: 'POST',
        body: { status: 'completed' }
      })
      wx.hideLoading()
      wx.showToast({ title: '打卡成功 ✓', icon: 'success' })
      this.loadHabits()
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '打卡失败', icon: 'none' })
    }
  },

  goToCreate() {
    wx.navigateTo({ url: '/pages/tasks/create?type=habit' })
  }
})