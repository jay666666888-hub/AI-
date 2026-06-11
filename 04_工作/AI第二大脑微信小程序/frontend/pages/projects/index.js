const app = getApp()

Page({
  data: {
    projects: [],
    newProjectTitle: '',
    showModal: false
  },

  onShow() {
    this.loadProjects()
  },

  async loadProjects() {
    try {
      const projects = await app.request('/projects')
      this.setData({ projects: projects || [] })
    } catch (e) {
      console.error('加载项目失败', e)
    }
  },

  showCreateModal() {
    this.setData({ showModal: true, newProjectTitle: '' })
  },

  hideModal() {
    this.setData({ showModal: false, newProjectTitle: '' })
  },

  preventTap() {},

  async confirmCreate() {
    const title = this.data.newProjectTitle.trim()
    if (!title) {
      wx.showToast({ title: '请输入项目名称', icon: 'none' })
      return
    }
    try {
      await app.request('/projects', {
        method: 'POST',
        body: { title, status: 'active' }
      })
      wx.showToast({ title: '创建成功', icon: 'success' })
      this.hideModal()
      this.loadProjects()
    } catch (e) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  onTitleInput(e) {
    this.setData({ newProjectTitle: e.detail.value })
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/projects/detail?id=${id}` })
  }
})
