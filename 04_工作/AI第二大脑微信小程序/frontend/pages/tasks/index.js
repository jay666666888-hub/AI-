const app = getApp()

const TASK_TYPES = ['全部', 'Todo', 'Habit', 'Schedule', 'Waiting']

Page({
  data: {
    currentType: '全部',
    taskTypes: TASK_TYPES,
    tasks: [],
    newTaskTitle: '',
    filterVisible: false,
    isBatchMode: false,
    selectedTasks: []
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
        const typeMap = { 'Todo': 'todo', 'Habit': 'habit', 'Schedule': 'schedule', 'Waiting': 'waiting' }
        url += `&type=${typeMap[currentType] || currentType.toLowerCase()}`
      }
      const res = await app.request(url)
      this.setData({ tasks: res || [] })
    } catch (e) {
      console.error('加载任务失败', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
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
      wx.showToast({ title: '创建成功 ✓', icon: 'success' })
      this.loadTasks()
    } catch (e) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  async completeTask(e) {
    const { id } = e.currentTarget.dataset
    // 找到任务
    const task = this.data.tasks.find(t => t.id === id)
    if (!task) return

    try {
      if (task.status === 'completed') {
        await app.request(`/tasks/${id}`, {
          method: 'PUT',
          body: { status: 'active' }
        })
        wx.showToast({ title: '已取消完成', icon: 'success' })
      } else {
        await app.request(`/tasks/${id}/complete`, { method: 'POST' })
        wx.showToast({ title: '已完成 ✓', icon: 'success' })
      }
      this.loadTasks()
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  async deleteTask(e) {
    const { id } = e.currentTarget.dataset
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个任务吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await app.request(`/tasks/${id}`, { method: 'DELETE' })
            wx.showToast({ title: '已删除', icon: 'success' })
            this.loadTasks()
          } catch (e) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 长按显示快捷操作菜单
  showQuickActions(e) {
    const { id, item } = e.currentTarget.dataset
    wx.showActionSheet({
      itemList: ['完成', '查看详情', '删除'],
      itemColor: '#3B82F6',
      success: (res) => {
        switch (res.tapIndex) {
          case 0: // 完成
            this.completeTask({ currentTarget: { dataset: { id } } })
            break
          case 1: // 查看详情
            this.goToDetail({ currentTarget: { dataset: { id } } })
            break
          case 2: // 删除
            this.deleteTask({ currentTarget: { dataset: { id } } })
            break
        }
      }
    })
  },

  // 批量选择相关
  toggleSelect(e) {
    const { id } = e.currentTarget.dataset
    const tasks = this.data.tasks.map(t => {
      if (t.id === id) {
        return { ...t, selected: !t.selected }
      }
      return t
    })
    const selectedTasks = tasks.filter(t => t.selected)
    this.setData({ tasks, selectedTasks })
  },

  cancelBatch() {
    const tasks = this.data.tasks.map(t => ({ ...t, selected: false }))
    this.setData({ isBatchMode: false, tasks, selectedTasks: [] })
  },

  async batchComplete() {
    const { selectedTasks } = this.data
    if (!selectedTasks.length) return

    wx.showLoading({ title: '处理中...' })
    try {
      for (const task of selectedTasks) {
        if (task.status !== 'completed') {
          await app.request(`/tasks/${task.id}/complete`, { method: 'POST' })
        }
      }
      wx.hideLoading()
      wx.showToast({ title: '批量完成 ✓', icon: 'success' })
      this.cancelBatch()
      this.loadTasks()
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '部分失败', icon: 'none' })
    }
  },

  async batchDelete() {
    const { selectedTasks } = this.data
    if (!selectedTasks.length) return

    wx.showModal({
      title: '确认删除',
      content: `确定要删除选中的 ${selectedTasks.length} 个任务吗？`,
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '处理中...' })
          try {
            for (const task of selectedTasks) {
              await app.request(`/tasks/${task.id}`, { method: 'DELETE' })
            }
            wx.hideLoading()
            wx.showToast({ title: '批量删除 ✓', icon: 'success' })
            this.cancelBatch()
            this.loadTasks()
          } catch (e) {
            wx.hideLoading()
            wx.showToast({ title: '部分失败', icon: 'none' })
          }
        }
      }
    })
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