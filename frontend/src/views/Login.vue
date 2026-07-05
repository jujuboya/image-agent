<template>
  <div class="login-container">
    <!-- 数据流动背景 -->
    <div class="data-flow-bg">
      <div v-for="i in 50" :key="i" class="data-particle" :style="getParticleStyle(i)"></div>
    </div>

    <!-- 主登录卡片 -->
    <div class="login-card">
      <!-- 左侧装饰区 -->
      <div class="card-decoration">
        <div class="decoration-circle"></div>
        <div class="decoration-line"></div>
        <div class="decoration-dots">
          <span v-for="i in 12" :key="i"></span>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="card-content">
        <div class="login-header">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1 class="title">{{ t('user.login') === 'Login' ? 'Image Dataset Agent' : '图片数据集智能采集' }}</h1>
          <p class="subtitle">{{ t('user.login') === 'Login' ? 'Agent System for AI Training' : 'Agent System for AI Training' }}</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="0"
          size="large"
          class="login-form"
        >
          <el-form-item prop="username">
            <div class="input-wrapper">
              <el-icon class="input-icon"><User /></el-icon>
              <el-input
                v-model="form.username"
                :placeholder="t('user.username')"
                class="custom-input"
              />
            </div>
          </el-form-item>

          <el-form-item prop="password">
            <div class="input-wrapper">
              <el-icon class="input-icon"><Lock /></el-icon>
              <el-input
                v-model="form.password"
                type="password"
                :placeholder="t('user.password')"
                show-password
                class="custom-input"
                @keyup.enter="handleLogin"
              />
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              <span class="btn-text">{{ t('user.login') }}</span>
              <span class="btn-icon">→</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <span class="footer-text">{{ t('user.login') === 'Login' ? 'No account?' : '还没有账号？' }}</span>
          <el-link type="primary" class="register-link" @click="showRegister = true">{{ t('user.register') }}</el-link>
        </div>

        <div class="system-info">
          <div class="info-item">
            <span class="info-dot"></span>
            <span>{{ t('user.login') === 'Login' ? 'AI Auto Labeling' : 'AI自动识别标签' }}</span>
          </div>
          <div class="info-item">
            <span class="info-dot"></span>
            <span>{{ t('user.login') === 'Login' ? 'Manual Review' : '人工审核纠错' }}</span>
          </div>
          <div class="info-item">
            <span class="info-dot"></span>
            <span>{{ t('user.login') === 'Login' ? 'Standard Export' : '标准化导出' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="用户注册" width="420px" class="register-dialog">
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="registerForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegister">
          注册
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/api'
import { t } from '../utils/i18n'

const router = useRouter()
const formRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  password: '',
  nickname: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于6个字符', trigger: 'blur' },
  ],
}

const getParticleStyle = (index: number) => {
  const delay = (index * 0.37) % 5
  const duration = 3 + ((index * 0.23) % 4)
  const left = (index * 13) % 100
  const size = 2 + (index % 4)
  return {
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    width: `${size}px`,
    height: `${size}px`,
  }
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res: any = await authApi.login(form.username, form.password)
    localStorage.setItem('token', res.access_token)
    const user: any = await authApi.getMe()
    localStorage.setItem('username', user.nickname || user.username)
    localStorage.setItem('userRole', user.role || 'viewer')
    ElMessage.success('登录成功')
    await router.replace('/dashboard')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return

  registerLoading.value = true
  try {
    await authApi.register(registerForm)
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    form.username = registerForm.username
    form.password = registerForm.password
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
  font-family: 'JetBrains Mono', monospace;
}

/* 数据流动背景 */
.data-flow-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.data-particle {
  position: absolute;
  bottom: -10px;
  background: linear-gradient(180deg, #3b82f6, #60a5fa);
  border-radius: 50%;
  opacity: 0.6;
  animation: floatUp linear infinite;
}

@keyframes floatUp {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100vh) translateX(20px);
    opacity: 0;
  }
}

/* 主登录卡片 */
.login-card {
  width: 900px;
  height: 520px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-radius: 20px;
  border: 1px solid var(--border-color);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 左侧装饰区 */
.card-decoration {
  width: 400px;
  background: linear-gradient(135deg, #1e3a5f 0%, var(--bg-tertiary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.decoration-circle {
  width: 200px;
  height: 200px;
  border: 2px solid #3b82f6;
  border-radius: 50%;
  position: relative;
  animation: pulse 3s ease-in-out infinite;

  &::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 20px;
    right: 20px;
    bottom: 20px;
    border: 1px solid #60a5fa;
    border-radius: 50%;
    animation: pulse 3s ease-in-out infinite 0.5s;
  }

  &::after {
    content: '';
    position: absolute;
    top: 40px;
    left: 40px;
    right: 40px;
    bottom: 40px;
    border: 1px solid #93c5fd;
    border-radius: 50%;
    animation: pulse 3s ease-in-out infinite 1s;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.decoration-line {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

.decoration-dots {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 300px;
  height: 300px;

  span {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #60a5fa;
    border-radius: 50%;
    animation: twinkle 2s ease-in-out infinite;

    @for $i from 1 through 12 {
      &:nth-child(#{$i}) {
        top: 50% + sin($i * 30deg) * 45%;
        left: 50% + cos($i * 30deg) * 45%;
        animation-delay: #{$i * 0.15}s;
      }
    }
  }
}

@keyframes twinkle {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.5);
  }
}

/* 右侧表单区 */
.card-content {
  flex: 1;
  padding: 50px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-header {
  margin-bottom: 40px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  color: #3b82f6;
  margin-bottom: 20px;
}

.title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
  letter-spacing: 1px;
}

/* 表单样式 */
.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }

  :deep(.el-form-item__content) {
    width: 100%;
  }
}

.input-wrapper {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 0 16px;
  transition: all 0.3s ease;

  &:focus-within {
    border-color: var(--border-hover);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
}

.input-icon {
  color: var(--text-tertiary);
  font-size: 18px;
  margin-right: 12px;
}

.custom-input {
  flex: 1;
  min-width: 0;
  width: 100%;

  :deep(.el-input__wrapper) {
    background: transparent !important;
    box-shadow: none !important;
    padding: 12px 0;
    width: 100%;
  }

  :deep(.el-input__inner) {
    background: transparent !important;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;

    &::placeholder {
      color: var(--text-tertiary);
    }

    &:-webkit-autofill,
    &:-webkit-autofill:hover,
    &:-webkit-autofill:focus,
    &:-webkit-autofill:active {
      -webkit-text-fill-color: var(--text-primary) !important;
      caret-color: var(--text-primary);
      box-shadow: 0 0 0 1000px var(--bg-tertiary) inset !important;
      transition: background-color 9999s ease-out 0s;
      font-family: 'JetBrains Mono', monospace;
    }
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-hover) 100%);
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
  }

  .btn-icon {
    font-size: 20px;
    transition: transform 0.3s ease;
  }

  &:hover .btn-icon {
    transform: translateX(4px);
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;

  .footer-text {
    color: var(--text-tertiary);
  }

  .register-link {
    font-weight: 500;
  }
}

.system-info {
  margin-top: 32px;
  display: flex;
  gap: 24px;
  justify-content: center;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.info-dot {
  width: 6px;
  height: 6px;
  background: var(--accent-color);
  border-radius: 50%;
}

/* 注册对话框 */
.register-dialog {
  :deep(.el-dialog) {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
  }

  :deep(.el-dialog__title) {
    color: var(--text-primary);
  }

  :deep(.el-form-item__label) {
    color: var(--text-secondary);
  }

  :deep(.el-input__wrapper) {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    box-shadow: none;

    &:hover {
      border-color: var(--border-hover);
    }

    &.is-focus {
      border-color: var(--border-hover);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }

  :deep(.el-input__inner) {
    color: var(--text-primary);
  }
}
</style>
