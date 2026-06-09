const app = getApp()
const api = require('../../utils/api')
const { getInboxCount } = api

Page({
  data: {
    inboxCount: 0,
    todayTimedTasks: [],
    todayFreeTasks: [],
    projects: []
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const inboxRes = await getInboxCount()
      this.setData({ inboxCount: inboxRes.count })

      const tasks = await api.getTasks({ status: 'active' })

      const timedTasks = tasks.filter(t => t.type === 'schedule' && t.scheduled_time)
        .sort((a, b) => a.scheduled_time.localeCompare(b.scheduled_time))

      const freeTasks = tasks.filter(t => t.type === 'todo' && !t.due_date)

      this.setData({
        todayTimedTasks: timedTasks,
        todayFreeTasks: freeTasks
      })

      const projects = await api.getProjects()
      const activeProjects = projects.filter(p => p.status === 'active').slice(0, 5)
      this.setData({ projects: activeProjects })

    } catch (e) {
      console.error('加载数据失败', e)
    }
  },

  goToInbox() {
    wx.navigateTo({ url: '/pages/tasks/index?type=inbox' })
  },

  goToProject(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/tasks/index?projectId=${id}` })
  },

  quickAdd() {
    wx.navigateTo({ url: '/pages/tasks/create' })
  }
})