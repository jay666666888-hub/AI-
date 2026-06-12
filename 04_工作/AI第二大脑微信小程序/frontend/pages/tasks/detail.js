const app = getApp()

Page({
  data: {
    taskId: null,
    task: {},
    loading: false
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ taskId: id })
      this.loadTask()
    }
  },

  async loadTask() {
    this.setData({ loading: true })
    try {
      const task = await app.request(`/tasks/${this.data.taskId}`)
      if (task) {
        this.setData({ task, loading: false })
      } else {
        this.setData({ loading: false })
        wx.showToast({ title: '任务不存在', icon: 'none' })
      }
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  async toggleComplete() {
    const { task } = this.data
    wx.showLoading({ title: '处理中...' })
    try {
      if (task.status === 'completed') {
        await app.request(`/tasks/${task.id}`, {
          method: 'PUT',
          body: { status: 'active' }
        })
        wx.hideLoading()
        wx.showToast({ title: '已取消完成 ✓', icon: 'success' })
      } else {
        await app.request(`/tasks/${task.id}/complete`, { method: 'POST' })
        wx.hideLoading()
        wx.showToast({ title: '已完成 ✓', icon: 'success' })
      }
      setTimeout(() => this.loadTask(), 500)
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  async deleteTask() {
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除吗？',
      confirmColor: '#ef4444',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' })
          try {
            await app.request(`/tasks/${this.data.taskId}`, { method: 'DELETE' })
            wx.hideLoading()
            wx.showToast({ title: '已删除 ✓', icon: 'success' })
            setTimeout(() => {
              wx.navigateBack()
            }, 1000)
          } catch (e) {
            wx.hideLoading()
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  }
})