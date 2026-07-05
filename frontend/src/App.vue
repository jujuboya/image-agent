<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { initTheme } from './utils/theme'

onMounted(() => {
  initTheme()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* Element Plus 主题全局覆盖 */
:root {
  --bg-primary: #0a0e17;
  --bg-secondary: #1a1f2e;
  --bg-tertiary: #0f172a;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --border-color: #1e293b;
  --border-hover: #3b82f6;
  --accent-color: #3b82f6;
  --accent-hover: #2563eb;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
}

[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-tertiary: #94a3b8;
  --border-color: #e2e8f0;
  --border-hover: #3b82f6;
  --accent-color: #3b82f6;
  --accent-hover: #2563eb;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
}

.el-input__wrapper {
  background-color: var(--bg-tertiary);
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--border-hover) inset;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--border-hover) inset;
}

.el-input__inner {
  color: var(--text-primary);
}

.el-input__inner::placeholder {
  color: var(--text-tertiary);
}

.el-textarea__inner {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.el-select .el-input__wrapper {
  background-color: var(--bg-tertiary) !important;
}

.el-input-number .el-input__wrapper {
  background-color: var(--bg-tertiary) !important;
}

/* 表格行hover效果 */
.el-table__row:hover {
  background-color: var(--bg-secondary) !important;
}

/* 卡片主题 */
.el-card {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

/* 标签主题 */
.el-tag {
  border-color: var(--border-color) !important;
}

/* 菜单主题 */
.el-menu {
  background-color: transparent !important;
  border-right: none !important;
}

.el-menu-item {
  color: var(--text-secondary) !important;
}

.el-menu-item:hover {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
}

.el-menu-item.is-active {
  background-color: var(--accent-color) !important;
  color: #fff !important;
}

/* 表格主题 */
.el-table {
  background-color: transparent !important;
  color: var(--text-primary) !important;
}

.el-table tr {
  background-color: transparent !important;
}

.el-table th.el-table__cell {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-secondary) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid var(--border-color) !important;
}

.el-table--enable-row-hover .el-table__body tr:hover>td.el-table__cell {
  background-color: var(--bg-secondary) !important;
}

.el-table__empty-text {
  color: var(--text-tertiary) !important;
}

/* 分页主题 */
.el-pagination {
  --el-pagination-bg-color: var(--bg-tertiary) !important;
  --el-pagination-text-color: var(--text-secondary) !important;
  --el-pagination-hover-color: var(--accent-color) !important;
}

.el-pager li {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-secondary) !important;
}

.el-pager li.is-active {
  background-color: var(--accent-color) !important;
  color: #fff !important;
}

.el-pagination .btn-prev,
.el-pagination .btn-next {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-secondary) !important;
}

/* 对话框主题 */
.el-dialog {
  background-color: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}

.el-dialog__title {
  color: var(--text-primary) !important;
}

.el-dialog__body {
  color: var(--text-secondary) !important;
}

/* 表单标签主题 */
.el-form-item__label {
  color: var(--text-secondary) !important;
}

/* 按钮主题 */
.el-button--default {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.el-button--default:hover {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-hover) !important;
  color: var(--text-primary) !important;
}

/* 下拉菜单主题 */
.el-select-dropdown {
  background-color: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}

.el-select-dropdown__item {
  color: var(--text-secondary) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
}

.el-select-dropdown__item.selected {
  color: var(--accent-color) !important;
}

/* 消息框主题 */
.el-message-box {
  background-color: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}

.el-message-box__title {
  color: var(--text-primary) !important;
}

.el-message-box__message {
  color: var(--text-secondary) !important;
}

/* 加载遮罩主题 */
.el-loading-mask {
  background-color: rgba(10, 14, 23, 0.8) !important;
}

[data-theme="light"] .el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8) !important;
}
</style>
