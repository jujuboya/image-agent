/**
 * 国际化工具
 */

export type Language = 'zh-cn' | 'en'

/**
 * 中文翻译
 */
const zhCn: Record<string, string> = {
  // 通用
  'common.confirm': '确定',
  'common.cancel': '取消',
  'common.save': '保存',
  'common.delete': '删除',
  'common.edit': '编辑',
  'common.search': '搜索',
  'common.reset': '重置',
  'common.refresh': '刷新',
  'common.loading': '加载中...',
  'common.success': '成功',
  'common.error': '错误',
  'common.warning': '警告',
  'common.info': '提示',

  // 导航
  'nav.dashboard': '数据看板',
  'nav.upload': '图片上传',
  'nav.images': '图片管理',
  'nav.review': '人工审核',
  'nav.dataset': '数据集管理',

  // 用户
  'user.login': '登录',
  'user.register': '注册',
  'user.logout': '退出登录',
  'user.profile': '个人中心',
  'user.settings': '系统设置',
  'user.username': '用户名',
  'user.password': '密码',
  'user.nickname': '昵称',
  'user.role': '角色',

  // 图片
  'image.upload': '上传图片',
  'image.batchUpload': '批量上传',
  'image.filename': '文件名',
  'image.size': '大小',
  'image.dimensions': '尺寸',
  'image.status': '状态',
  'image.createdAt': '上传时间',
  'image.actions': '操作',
  'image.detail': '详情',
  'image.delete': '删除',

  // 标签
  'label.season': '季节',
  'label.timePeriod': '时段',
  'label.dayType': '工作日',
  'label.weather': '天气',
  'label.temperature': '温度',
  'label.humidity': '湿度',
  'label.light': '光照',
  'label.shootAngle': '拍摄角度',
  'label.sceneScale': '景别',
  'label.clarity': '清晰度',
  'label.exposure': '曝光',
  'label.sceneType': '场景类型',
  'label.deviceType': '设备类型',
  'label.province': '省',
  'label.city': '市',
  'label.district': '区',
  'label.address': '地址',

  // 设置
  'settings.title': '系统设置',
  'settings.theme': '主题模式',
  'settings.theme.dark': '深色模式',
  'settings.theme.light': '浅色模式',
  'settings.language': '语言',
  'settings.imageQuality': '图片质量',
  'settings.autoParse': '自动解析',
  'settings.autoParse.desc': '上传后自动解析图片',

  // 消息
  'notification.title': '消息通知',
  'notification.unread': '未读消息',
  'notification.markAllRead': '全部标为已读',
}

/**
 * 英文翻译
 */
const en: Record<string, string> = {
  // General
  'common.confirm': 'Confirm',
  'common.cancel': 'Cancel',
  'common.save': 'Save',
  'common.delete': 'Delete',
  'common.edit': 'Edit',
  'common.search': 'Search',
  'common.reset': 'Reset',
  'common.refresh': 'Refresh',
  'common.loading': 'Loading...',
  'common.success': 'Success',
  'common.error': 'Error',
  'common.warning': 'Warning',
  'common.info': 'Info',

  // Navigation
  'nav.dashboard': 'Dashboard',
  'nav.upload': 'Upload',
  'nav.images': 'Images',
  'nav.review': 'Review',
  'nav.dataset': 'Dataset',

  // User
  'user.login': 'Login',
  'user.register': 'Register',
  'user.logout': 'Logout',
  'user.profile': 'Profile',
  'user.settings': 'Settings',
  'user.username': 'Username',
  'user.password': 'Password',
  'user.nickname': 'Nickname',
  'user.role': 'Role',

  // Image
  'image.upload': 'Upload Image',
  'image.batchUpload': 'Batch Upload',
  'image.filename': 'Filename',
  'image.size': 'Size',
  'image.dimensions': 'Dimensions',
  'image.status': 'Status',
  'image.createdAt': 'Created At',
  'image.actions': 'Actions',
  'image.detail': 'Detail',
  'image.delete': 'Delete',

  // Label
  'label.season': 'Season',
  'label.timePeriod': 'Time Period',
  'label.dayType': 'Day Type',
  'label.weather': 'Weather',
  'label.temperature': 'Temperature',
  'label.humidity': 'Humidity',
  'label.light': 'Light',
  'label.shootAngle': 'Shoot Angle',
  'label.sceneScale': 'Scene Scale',
  'label.clarity': 'Clarity',
  'label.exposure': 'Exposure',
  'label.sceneType': 'Scene Type',
  'label.deviceType': 'Device Type',
  'label.province': 'Province',
  'label.city': 'City',
  'label.district': 'District',
  'label.address': 'Address',

  // Settings
  'settings.title': 'Settings',
  'settings.theme': 'Theme Mode',
  'settings.theme.dark': 'Dark Mode',
  'settings.theme.light': 'Light Mode',
  'settings.language': 'Language',
  'settings.imageQuality': 'Image Quality',
  'settings.autoParse': 'Auto Parse',
  'settings.autoParse.desc': 'Auto parse images after upload',

  // Notification
  'notification.title': 'Notifications',
  'notification.unread': 'Unread',
  'notification.markAllRead': 'Mark all as read',
}

const messages: Record<Language, Record<string, string>> = {
  'zh-cn': zhCn,
  'en': en,
}

/**
 * 获取当前语言
 */
export function getLanguage(): Language {
  return (localStorage.getItem('language') as Language) || 'zh-cn'
}

/**
 * 设置语言
 */
export function setLanguage(lang: Language): void {
  localStorage.setItem('language', lang)
}

/**
 * 翻译
 */
export function t(key: string): string {
  const lang = getLanguage()
  return messages[lang]?.[key] || messages['zh-cn']?.[key] || key
}
