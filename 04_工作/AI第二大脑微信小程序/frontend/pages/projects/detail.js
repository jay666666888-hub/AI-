const app = getApp()

Page({
  data: {
    projectId: null,
    project: {},
    tasks: []
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ projectId: id })
      this.loadProject()
      this.loadTasks()
    }
  },

  async loadProject() {
    try {
      const res = await app.request(`/projects/${this.data.projectId}`)
      this.setData({ project: res })
    } catch (e) {
      console.error('加载项目失败', e)
    }
  },

  async loadTasks() {
    try {
      // 获取该项目下的任务
      const res = await app.request(`/tasks?project_id=${this.data.projectId}&status=active`)
      this.setData({ tasks: res || [] })
    } catch (e) {
      console.error('加载任务失败', e)
    }
  },

  async toggleTask(e) {
    const { id } = e.currentTarget.dataset
    const { tasks } = this.data
    const task = tasks.find(t => t.id === id)
    if (!task) return

    try {
      if (task.status === 'completed') {
        // 取消完成
        await app.request(`/tasks/${id}`, {
          method: 'PATCH',
          body: { status: 'active' }
        })
      } else {
        await app.request(`/tasks/${id}/complete`, { method: 'POST' })
      }
      this.loadTasks()
      this.loadProject() // 刷新进度
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  goToCreateTask() {
    wx.navigateTo({
      url: `/pages/tasks/create?projectId=${this.data.projectId}`
    })
  }
})