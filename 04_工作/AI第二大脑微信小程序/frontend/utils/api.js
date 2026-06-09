const app = getApp()

module.exports = {
  wxLogin: (code) => app.request('/auth/wx-login', { method: 'POST', body: { code } }),
  getProjects: () => app.request('/projects'),
  createProject: (data) => app.request('/projects', { method: 'POST', body: data }),
  updateProject: (id, data) => app.request(`/projects/${id}`, { method: 'PUT', body: data }),
  getTasks: (params) => app.request('/tasks?' + new URLSearchParams(params)),
  createTask: (data) => app.request('/tasks', { method: 'POST', body: data }),
  updateTask: (id, data) => app.request(`/tasks/${id}`, { method: 'PUT', body: data }),
  completeTask: (id) => app.request(`/tasks/${id}/complete`, { method: 'POST' }),
  getNotes: (status) => app.request('/notes' + (status ? `?status=${status}` : '')),
  createNote: (data) => app.request('/notes', { method: 'POST', body: data }),
  updateNote: (id, data) => app.request(`/notes/${id}`, { method: 'PUT', body: data }),
  getInboxCount: () => app.request('/notes/inbox/count'),
  logHabit: (taskId, data) => app.request(`/tasks/habits/${taskId}/log`, { method: 'POST', body: data }),
  getHabitStats: (taskId) => app.request(`/tasks/habits/${taskId}/stats`)
}