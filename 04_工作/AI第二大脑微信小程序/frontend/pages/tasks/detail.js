const app = getApp()

Page({
  data: {
    taskId: null,
    task: {}
  },

  onLoad(options) {
    console.log('detail options:', options)
    const { id } = options
    if (id) {
      this.setData({ taskId: id })
      this.loadTask()
    }
  },

  async loadTask() {
    try {
      // 直接获取单个任务详情
      const task = await app.request(`/tasks/${this.data.taskId}`)
      if (task) {
        this.setData({ task })
      } else {
        console.error('任务不存在')
      }
    } catch (e) {
      console.error('加载任务失败', e)
    }
  },

  async toggleComplete() {
    const { task } = this.data
    try {
      if (task.status === 'completed') {
        await app.request(`/tasks/${task.id}`, {
          method: 'PATCH',
          body: { status: 'active' }
        })
        wx.showToast({ title: '已取消完成', icon: 'success' })
      } else {
        await app.request(`/tasks/${task.id}/complete`, { method: 'POST' })
        wx.showToast({ title: '已完成', icon: 'success' })
      }
      this.loadTask()
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  async deleteTask() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个任务吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await app.request(`/tasks/${this.data.taskId}`, { method: 'DELETE' })
            wx.showToast({ title: '已删除', icon: 'success' })
            setTimeout(() => {
              wx.navigateBack()
            }, 1000)
          } catch (e) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  }
})