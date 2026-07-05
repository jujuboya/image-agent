<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '72px' : '260px'" class="aside">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <transition name="fade">
          <span v-show="!isCollapse" class="title">数据集采集系统</span>
        </transition>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        router
        class="side-menu"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
          class="menu-item"
        >
          <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
          <template #title>
            <span class="menu-text">{{ t(item.titleKey) }}</span>
          </template>
        </el-menu-item>
      </el-menu>

      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon>
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <div class="breadcrumb-area">
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>

        <div class="header-right">
          <div class="header-actions">
            <div class="action-item" @click="showNotifications">
              <el-icon><Bell /></el-icon>
              <span class="action-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
            </div>
            <div class="action-item" @click="showSettings = true">
              <el-icon><Setting /></el-icon>
            </div>
          </div>

          <el-divider direction="vertical" />

          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <div class="user-avatar">
                <el-icon><User /></el-icon>
              </div>
              <div class="user-details">
                <span class="username">{{ username }}</span>
                <span class="user-role">{{ roleLabel }}</span>
              </div>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown">
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>{{ t('user.profile') }}</span>
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  <span>{{ t('user.settings') }}</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>{{ t('user.logout') }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>

  <!-- 设置对话框 -->
  <el-dialog v-model="showSettings" :title="t('settings.title')" width="500px">
    <el-form label-width="100px">
      <el-form-item :label="t('settings.theme')">
        <el-radio-group v-model="themeMode">
          <el-radio label="dark">{{ t('settings.theme.dark') }}</el-radio>
          <el-radio label="light">{{ t('settings.theme.light') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="t('settings.language')">
        <el-select v-model="language">
          <el-option label="简体中文" value="zh-cn" />
          <el-option label="English" value="en" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('settings.imageQuality')">
        <el-slider v-model="imageQuality" :min="1" :max="100" :format-tooltip="(val: number) => `${val}%`" />
      </el-form-item>
      <el-form-item :label="t('settings.autoParse')">
        <el-switch v-model="autoParse" />
        <span class="setting-desc">{{ t('settings.autoParse.desc') }}</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showSettings = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="saveSettings">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTheme, setTheme, applyTheme, type ThemeMode } from '../utils/theme'
import { getLanguage, setLanguage, type Language, t } from '../utils/i18n'

const route = useRoute()
const router = useRouter()

const isCollapse = ref(false)
const username = ref(localStorage.getItem('username') || '用户')
const userRole = ref(localStorage.getItem('userRole') || 'viewer')
const showSettings = ref(false)
const unreadCount = ref(0)

const notifications = ref<any[]>([])

const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    admin: '管理员',
    editor: '编辑员',
    viewer: '查看者',
  }
  return labels[userRole.value] || userRole.value
})

const themeMode = ref<ThemeMode>(getTheme())
const language = ref<Language>(getLanguage())
const imageQuality = ref(Number(localStorage.getItem('imageQuality')) || 80)
const autoParse = ref(localStorage.getItem('autoParse') !== 'false')

// 初始化主题
applyTheme(themeMode.value)

// 监听主题变化
watch(themeMode, (newTheme) => {
  setTheme(newTheme)
  applyTheme(newTheme)
})

// 监听语言变化
watch(language, (newLang) => {
  setLanguage(newLang)
  ElMessage.success(newLang === 'en' ? 'Language changed, refresh to apply' : '语言已切换，刷新后生效')
})

const menuItems = ref([
  { path: '/dashboard', titleKey: 'nav.dashboard', icon: 'DataBoard' },
  { path: '/upload', titleKey: 'nav.upload', icon: 'Upload' },
  { path: '/images', titleKey: 'nav.images', icon: 'Picture' },
  { path: '/review', titleKey: 'nav.review', icon: 'Checked' },
  { path: '/dataset', titleKey: 'nav.dataset', icon: 'FolderOpened' },
])

const handleCommand = (command: string) => {
  if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
    router.push('/login')
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中...')
  } else if (command === 'settings') {
    showSettings.value = true
  }
}

const showNotifications = () => {
  if (notifications.value.length === 0) {
    ElMessage.info('暂无新的系统通知')
    return
  }
  ElMessageBox.alert(
    notifications.value.map(n => `【${n.title}】${n.content} - ${n.time}`).join('\n\n'),
    '消息通知',
    { confirmButtonText: '知道了' }
  )
  unreadCount.value = 0
}

const saveSettings = () => {
  // 保存设置到 localStorage
  localStorage.setItem('themeMode', themeMode.value)
  localStorage.setItem('language', language.value)
  localStorage.setItem('imageQuality', imageQuality.value.toString())
  localStorage.setItem('autoParse', autoParse.value.toString())

  showSettings.value = false
  ElMessage.success('设置已保存')
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.layout-container {
  height: 100vh;
  font-family: 'JetBrains Mono', monospace;
}

/* 侧边栏 */
.aside {
  background: linear-gradient(180deg, var(--bg-tertiary) 0%, var(--bg-primary) 100%);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, #1e3a5f 0%, var(--bg-tertiary) 100%);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--accent-color);
  flex-shrink: 0;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  letter-spacing: 1px;
}

.side-menu {
  border-right: none;
  flex: 1;
  padding: 12px 0;
  background: transparent;

  :deep(.el-menu-item) {
    height: 52px;
    margin: 4px 12px;
    border-radius: 12px;
    color: var(--text-secondary);

    &:hover {
      background: linear-gradient(135deg, #1e3a5f 0%, var(--bg-secondary) 100%);
      color: var(--text-primary);
    }

    &.is-active {
      background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-hover) 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
  }
}

.menu-icon {
  font-size: 20px;
  margin-right: 12px;
}

.menu-text {
  font-size: 14px;
  font-weight: 500;
}

.collapse-btn {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  cursor: pointer;
  border-top: 1px solid var(--border-color);
  transition: all 0.3s ease;

  &:hover {
    color: var(--accent-color);
    background: var(--bg-secondary);
  }
}

/* 顶部栏 */
.header {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 72px;
}

.breadcrumb-area {
  display: flex;
  align-items: center;
  gap: 16px;
}

.breadcrumb {
  :deep(.el-breadcrumb__inner) {
    color: var(--text-secondary);
    font-weight: 400;
  }

  :deep(.el-breadcrumb__separator) {
    color: var(--text-tertiary);
  }

  :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
    color: var(--text-primary);
    font-weight: 500;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-item {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .el-icon {
    font-size: 20px;
  }
}

.action-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 16px;
  height: 16px;
  background: #ef4444;
  border-radius: 50%;
  font-size: 10px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider--vertical {
  border-left: 1px solid var(--border-color);
  height: 32px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 12px;
  transition: all 0.3s ease;

  &:hover {
    background: var(--bg-secondary);
  }
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-hover) 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 11px;
  color: var(--text-tertiary);
}

.dropdown-icon {
  color: var(--text-tertiary);
  font-size: 14px;
}

.setting-desc {
  margin-left: 10px;
  font-size: 12px;
  color: #64748b;
}

/* 用户下拉菜单 */
.user-dropdown {
  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
  }
}

/* 主内容区 */
.main {
  background: var(--bg-primary);
  padding: 24px;
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
