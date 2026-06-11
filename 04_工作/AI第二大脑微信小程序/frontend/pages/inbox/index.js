const app = getApp()

Page({
  data: {
    notes: [],
    newNoteText: ''
  },

  onLoad() {
    this.loadNotes()
  },

  onShow() {
    this.loadNotes()
  },

  async loadNotes() {
    try {
      const res = await app.request('/notes?status=inbox')
      this.setData({ notes: res || [] })
    } catch (e) {
      console.error('加载笔记失败', e)
    }
  },

  async createNote() {
    const text = this.data.newNoteText.trim()
    if (!text) {
      wx.showToast({ title: '请输入内容', icon: 'none' })
      return
    }
    try {
      await app.request('/notes', {
        method: 'POST',
        body: { content: text, status: 'inbox' }
      })
      this.setData({ newNoteText: '' })
      wx.showToast({ title: '已添加到Inbox', icon: 'success' })
      this.loadNotes()
    } catch (e) {
      wx.showToast({ title: '创建失败', icon: 'none' })
    }
  },

  async deleteNote(e) {
    const { id } = e.currentTarget.dataset
    try {
      await app.request(`/notes/${id}`, { method: 'DELETE' })
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadNotes()
    } catch (e) {
      wx.showToast({ title: '删除失败', icon: 'none' })
    }
  },

  onInput(e) {
    this.setData({ newNoteText: e.detail.value })
  },

  // 长按显示转化菜单
  showActionSheet(e) {
    const { id, content } = e.currentTarget.dataset

    wx.showActionSheet({
      itemList: ['转任务', '转项目', '转记忆', '删除'],
      success: (res) => {
        switch (res.tapIndex) {
          case 0:  // 转任务
            this.convertToTask(id, content)
            break
          case 1:  // 转项目
            this.convertToProject(id, content)
            break
          case 2:  // 转记忆
            this.convertToMemory(id, content)
            break
          case 3:  // 删除
            this.deleteNote({ currentTarget: { dataset: { id } } })
            break
        }
      }
    })
  },

  // 快速转任务（内容预填）
  async convertToTask(noteId, content) {
    // 先删除 inbox 笔记
    try {
      await app.request(`/notes/${noteId}`, { method: 'DELETE' })
    } catch (e) {
      console.error('删除笔记失败', e)
    }

    // 跳转到创建任务页，内容作为标题
    const encodedContent = encodeURIComponent(content)
    wx.navigateTo({
      url: `/pages/tasks/create?title=${encodedContent}&from=inbox`
    })
  },

  // 快速转项目（内容预填）
  async convertToProject(noteId, content) {
    // 先删除 inbox 笔记
    try {
      await app.request(`/notes/${noteId}`, { method: 'DELETE' })
    } catch (e) {
      console.error('删除笔记失败', e)
    }

    // 跳转到创建项目页
    const encodedContent = encodeURIComponent(content)
    wx.navigateTo({
      url: `/pages/projects/create?title=${encodedContent}&from=inbox`
    })
  },

  // 快速转记忆（内容预填）
  async convertToMemory(noteId, content) {
    // 直接创建记忆
    try {
      await app.request('/memories', {
        method: 'POST',
        body: {
          title: content.length > 50 ? content.substring(0, 50) + '...' : content,
          content: content
        }
      })
      // 删除 inbox 笔记
      await app.request(`/notes/${noteId}`, { method: 'DELETE' })
      wx.showToast({ title: '已转为记忆', icon: 'success' })
      this.loadNotes()
    } catch (e) {
      wx.showToast({ title: '转化失败', icon: 'none' })
    }
  }
})