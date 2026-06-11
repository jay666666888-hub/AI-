const app = getApp()

const TASK_TYPES = ['全部', 'Todo', 'Habit', 'Schedule', 'Waiting']

Page({
  data: {
    currentType: '全部',
    taskTypes: TASK_TYPES,
    tasks: [],
    newTaskTitle: '',
    filterVisible: false
  },

  onLoad() {
    this.loadTasks()
  },

  onShow() {
    this.loadTasks()
  },

  onPullDownRefresh() {
    this.loadTasks().then(() => wx.stopPullDownRefresh())
  },

  async loadTasks() {
    try {
      const { currentType } = this.data
      let url = '/tasks?status=active'
      if (currentType !== '全部') {
        // API expects lowercase type: todo, habit, schedule, waiting
        const typeMap = { 'Todo': 'todo', 'Habit': 'habit', 'Schedule': 'schedule', 'Waiting': 'waiting' }
        url += `&type=${typeMap[currentType] || currentType.toLowerCase()}`
      }
      const res = await app.request(url)
      this.setData({ tasks: res || [] })
    } catch (e) {
      console.error('加载任务失败', e)
    }
  },

  switchType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ currentType: type })
    this.loadTasks()
  },

  async createTask() {
    const title = this.data.newTaskTitle.trim()
    if (!title) {
      wx.showToast({ title: '请输入任务标题', icon: 'none' })
      return
    }
    try {
      await app.request('/tasks', {
        method: 'POST',
        body: { title, type: 'todo', status: 'active' }
      })
      this.setData({ newTaskTitle: '' })
      wx.showToast({ title: '创建成功', icon: 'success' })
      this.loadTasks()
    } catch (e) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  async completeTask(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/tasks/${id}/complete`, { method: 'POST' })
      wx.showToast({ title: '已完成', icon: 'success' })
      this.loadTasks()
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  async deleteTask(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/tasks/${id}`, { method: 'DELETE' })
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadTasks()
    } catch (e) {
      wx.showToast({ title: '删除失败', icon: 'none' })
    }
  },

  goToCreate() {
    wx.navigateTo({ url: '/pages/tasks/create' })
  },

  onTitleInput(e) {
    this.setData({ newTaskTitle: e.detail.value })
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/tasks/detail?id=${id}` })
  }
})
