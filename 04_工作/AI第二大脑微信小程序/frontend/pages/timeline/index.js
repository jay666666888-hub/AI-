const app = getApp()

// 工具函数：格式化日期
function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 工具函数：获取中文日期字符串
function formatDateStr(date) {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekday = weekdays[date.getDay()]
  return `${year}年${month}月${day}日 ${weekday}`
}

// 获取某月的第一天是星期几 (0-6)
function getFirstDayOfMonth(year, month) {
  return new Date(year, month - 1, 1).getDay()
}

// 获取某月的总天数
function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate()
}

// 判断两个日期是否是同一天
function isSameDay(d1, d2) {
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate()
}

// 判断日期是否在数组中
function dateInArray(date, dateArray) {
  const dateStr = formatDate(date)
  return dateArray.includes(dateStr)
}

Page({
  data: {
    currentYear: 0,
    currentMonth: 0,
    selectedDate: null,        // 选中的日期 (Date对象)
    selectedDateStr: '',      // 显示用的日期字符串
    weekdays: ['日', '一', '二', '三', '四', '五', '六'],
    calendarDays: [],         // 日历天的数据
    logs: [],
    datesWithLogs: []         // 有日志的日期数组
  },

  onLoad() {
    const now = new Date()
    this.setData({
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1,
      selectedDate: now,
      selectedDateStr: formatDateStr(now)
    })
    this.renderCalendar()
    this.loadLogs()
    this.loadDatesWithLogs()
  },

  onShow() {
    this.loadLogs()
    this.loadDatesWithLogs()
  },

  // 加载有日志的日期列表 (用于显示圆点)
  loadDatesWithLogs() {
    const token = wx.getStorageSync('token')
    if (!token) return

    // 获取本月的日期范围
    const year = this.data.currentYear
    const month = this.data.currentMonth
    const firstDay = new Date(year, month - 1, 1)
    const lastDay = new Date(year, month, 0)

    const startDate = formatDate(firstDay)
    const endDate = formatDate(lastDay)

    wx.request({
      url: `${app.globalData.apiBaseUrl}/daily-logs/dates`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      data: {
        start_date: startDate,
        end_date: endDate
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          this.setData({ datesWithLogs: res.data.dates || [] })
          this.renderCalendar()
        }
      },
      fail: (err) => {
        console.error('加载日志日期失败', err)
      }
    })
  },

  // 渲染日历
  renderCalendar() {
    const year = this.data.currentYear
    const month = this.data.currentMonth
    const today = new Date()
    const selectedDate = this.data.selectedDate
    const datesWithLogs = this.data.datesWithLogs

    const firstDay = getFirstDayOfMonth(year, month)
    const daysInMonth = getDaysInMonth(year, month)
    const daysInPrevMonth = getDaysInMonth(year, month - 1)

    const calendarDays = []

    // 上月的日期 (填充空白)
    for (let i = 0; i < firstDay; i++) {
      const day = daysInPrevMonth - firstDay + i + 1
      const date = new Date(year, month - 2, day)
      calendarDays.push({
        day: day,
        date: date,
        dateStr: formatDate(date),
        isToday: isSameDay(date, today),
        isSelected: isSameDay(date, selectedDate),
        hasLogs: dateInArray(date, datesWithLogs),
        isCurrentMonth: false
      })
    }

    // 本月的日期
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month - 1, day)
      calendarDays.push({
        day: day,
        date: date,
        dateStr: formatDate(date),
        isToday: isSameDay(date, today),
        isSelected: isSameDay(date, selectedDate),
        hasLogs: dateInArray(date, datesWithLogs),
        isCurrentMonth: true
      })
    }

    // 下月的日期 (填充空白，保持6行)
    const remainingCells = 42 - calendarDays.length
    for (let i = 1; i <= remainingCells; i++) {
      const date = new Date(year, month, i)
      calendarDays.push({
        day: i,
        date: date,
        dateStr: formatDate(date),
        isToday: isSameDay(date, today),
        isSelected: isSameDay(date, selectedDate),
        hasLogs: dateInArray(date, datesWithLogs),
        isCurrentMonth: false
      })
    }

    this.setData({ calendarDays })
  },

  // 上个月
  prevMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 1) {
      currentMonth = 12
      currentYear--
    } else {
      currentMonth--
    }
    this.setData({
      currentYear,
      currentMonth
    })
    this.renderCalendar()
    this.loadDatesWithLogs()
  },

  // 下个月
  nextMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 12) {
      currentMonth = 1
      currentYear++
    } else {
      currentMonth++
    }
    this.setData({
      currentYear,
      currentMonth
    })
    this.renderCalendar()
    this.loadDatesWithLogs()
  },

  // 选择日期
  selectDate(e) {
    const dateStr = e.currentTarget.dataset.date
    const date = new Date(dateStr)
    this.setData({
      selectedDate: date,
      selectedDateStr: formatDateStr(date)
    })
    this.renderCalendar()
    this.loadLogs()
  },

  // 加载选中日期的日志
  loadLogs() {
    const token = wx.getStorageSync('token')
    if (!token) return

    const dateStr = formatDate(this.data.selectedDate)

    wx.request({
      url: `${app.globalData.apiBaseUrl}/daily-logs`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      data: {
        log_date: dateStr
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          this.setData({ logs: res.data.logs || [] })
        }
      },
      fail: (err) => {
        console.error('加载日志失败', err)
      }
    })
  }
})