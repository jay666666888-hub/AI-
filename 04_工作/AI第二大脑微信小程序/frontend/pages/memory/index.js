const app = getApp()

Page({
  data: {
    memories: [],
    searchText: ''
  },

  onLoad() {
    this.loadMemories()
  },

  onShow() {
    this.loadMemories()
  },

  async loadMemories() {
    try {
      const res = await app.request('/notes?status=archived')
      this.setData({ memories: res || [] })
    } catch (e) {
      console.error('加载记忆失败', e)
    }
  },

  onSearch(e) {
    this.setData({ searchText: e.detail.value })
  }
})
