/**
 * 主题管理工具
 */

export type ThemeMode = 'dark' | 'light'

/**
 * 获取当前主题
 */
export function getTheme(): ThemeMode {
  return (localStorage.getItem('themeMode') as ThemeMode) || 'dark'
}

/**
 * 设置主题
 */
export function setTheme(theme: ThemeMode): void {
  localStorage.setItem('themeMode', theme)
  document.documentElement.setAttribute('data-theme', theme)
}

/**
 * 初始化主题
 */
export function initTheme(): void {
  const theme = getTheme()
  document.documentElement.setAttribute('data-theme', theme)
}

/**
 * 浅色主题变量
 */
export const lightTheme = {
  '--bg-primary': '#ffffff',
  '--bg-secondary': '#f8fafc',
  '--bg-tertiary': '#f1f5f9',
  '--text-primary': '#1e293b',
  '--text-secondary': '#475569',
  '--text-tertiary': '#94a3b8',
  '--border-color': '#e2e8f0',
  '--border-hover': '#3b82f6',
  '--accent-color': '#3b82f6',
  '--accent-hover': '#2563eb',
  '--success-color': '#10b981',
  '--warning-color': '#f59e0b',
  '--danger-color': '#ef4444',
  '--shadow-color': 'rgba(0, 0, 0, 0.1)',
}

/**
 * 深色主题变量
 */
export const darkTheme = {
  '--bg-primary': '#0a0e17',
  '--bg-secondary': '#1a1f2e',
  '--bg-tertiary': '#0f172a',
  '--text-primary': '#f1f5f9',
  '--text-secondary': '#94a3b8',
  '--text-tertiary': '#64748b',
  '--border-color': '#1e293b',
  '--border-hover': '#3b82f6',
  '--accent-color': '#3b82f6',
  '--accent-hover': '#2563eb',
  '--success-color': '#10b981',
  '--warning-color': '#f59e0b',
  '--danger-color': '#ef4444',
  '--shadow-color': 'rgba(0, 0, 0, 0.3)',
}

/**
 * 应用主题变量
 */
export function applyTheme(theme: ThemeMode): void {
  const root = document.documentElement
  const themeVars = theme === 'dark' ? darkTheme : lightTheme

  Object.entries(themeVars).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
}
