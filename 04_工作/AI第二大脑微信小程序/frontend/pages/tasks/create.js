const app = getApp()

Page({
  data: {
    title: '',
    type: 'todo',
    priority: 3,
    detail: '',
    projectId: null,
    projects: [],
    selectedProjectTitle: ''
  },

  onLoad(options) {
    this.loadProjects()
    // 如果有 projectId 参数，自动选中项目
    if (options.projectId) {
      this.setData({ projectId: options.projectId })
    }
  },

  async loadProjects() {
    try {
      const projects = await app.request('/projects')
      this.setData({ projects: projects || [] })
    } catch (e) {
      console.error('加载项目失败', e)
    }
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value })
  },

  onDetailInput(e) {
    this.setData({ detail: e.detail.value })
  },

  selectType(e) {
    this.setData({ type: e.currentTarget.dataset.type })
  },

  selectPriority(e) {
    this.setData({ priority: parseInt(e.currentTarget.dataset.priority) })
  },

  onProjectChange(e) {
    const index = e.detail.value
    if (index > 0) {
      const project = this.data.projects[index - 1]
      this.setData({
        projectId: project.id,
        selectedProjectTitle: project.title
      })
    } else {
      this.setData({ projectId: null, selectedProjectTitle: '' })
    }
  },

  async onSubmit() {
    const title = this.data.title.trim()
    if (!title) {
      wx.showToast({ title: '请输入任务标题', icon: 'none' })
      return
    }

    try {
      await app.request('/tasks', {
        method: 'POST',
        body: {
          title,
          type: this.data.type,
          priority: this.data.priority,
          detail: this.data.detail,
          project_id: this.data.projectId,
          status: 'active'
        }
      })
      wx.showToast({ title: '创建成功', icon: 'success' })
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)
    } catch (e) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  onClose() {
    wx.navigateBack()
  }
})