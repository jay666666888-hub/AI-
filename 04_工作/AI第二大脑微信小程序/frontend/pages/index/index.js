const app = getApp()

Page({
  data: {
    userInfo: null,
    inboxCount: 0,
    completedToday: 0,
    streak: 0,
    todayTasks: [],
    activeProjects: [],
    todayHabits: []
  },

  onLoad() {
    if (!app.globalData.token) {
      this.doLogin()
    }
  },

  onShow() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  async doLogin() {
    try {
      await app.login()
      this.loadData()
    } catch (e) {
      console.error('登录失败', e)
      wx.showToast({ title: '登录失败', icon: 'none' })
    }
  },

  async loadData() {
    try {
      const [inboxRes, tasksRes, projectsRes] = await Promise.all([
        app.request('/notes/inbox/count'),
        app.request('/tasks?status=active'),
        app.request('/projects')
      ])

      let habitsData = { habits: [], streak: 0 }
      try {
        habitsData = await app.request('/tasks/habits/today')
      } catch (e) {
        console.log('习惯接口暂无数据')
      }

      const completedToday = (tasksRes || []).filter(t => t.status === 'completed').length

      this.setData({
        inboxCount: inboxRes.count || 0,
        todayTasks: tasksRes || [],
        activeProjects: projectsRes || [],
        todayHabits: habitsData.habits || [],
        completedToday,
        streak: habitsData.streak || 0
      })
    } catch (e) {
      console.error('加载数据失败', e)
    }
  },

  async completeTask(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/tasks/${id}/complete`, { method: 'POST' })
      wx.showToast({ title: '已完成', icon: 'success' })
      this.loadData()
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  goToInbox() {
    wx.navigateTo({ url: '/pages/inbox/index' })
  },

  goToTasks() {
    wx.switchTab({ url: '/pages/tasks/index' })
  },

  goToProjects() {
    wx.switchTab({ url: '/pages/projects/index' })
  },

  goToHabits() {
    wx.navigateTo({ url: '/pages/habits/index' })
  }
})
