<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-side">
      <div class="brand-content">
        <div class="brand-logo">
          <svg viewBox="0 0 48 48" width="48" height="48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="12" fill="rgba(255,255,255,0.15)"/>
            <path d="M12 24L21 15L30 24L21 33Z" fill="white" opacity="0.9"/>
            <path d="M21 15L30 24L39 15" stroke="white" stroke-width="2" opacity="0.6"/>
          </svg>
        </div>
        <h1 class="brand-title">自动化竞品分析<br/>与市场情报系统</h1>
        <p class="brand-desc">Competitive Intelligence & Market Analysis Platform</p>

        <!-- 特性列表 -->
        <div class="feature-list">
          <div class="feature-item">
            <el-icon :size="20"><Monitor /></el-icon>
            <div>
              <div class="feature-name">自动采集</div>
              <div class="feature-desc">RSS / API / 爬虫多源采集</div>
            </div>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><MagicStick /></el-icon>
            <div>
              <div class="feature-name">AI 智能分析</div>
              <div class="feature-desc">情感分析、摘要提取、报告生成</div>
            </div>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><Bell /></el-icon>
            <div>
              <div class="feature-name">实时预警</div>
              <div class="feature-desc">关键词监控，出事即刻提醒</div>
            </div>
          </div>
          <div class="feature-item">
            <el-icon :size="20"><TrendCharts /></el-icon>
            <div>
              <div class="feature-name">数据可视化</div>
              <div class="feature-desc">情报分布、趋势、对比一目了然</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="form-side">
      <div class="login-card">
        <div class="login-header">
          <h2>欢迎回来</h2>
          <p>登录以访问竞品分析平台</p>
        </div>

        <el-tabs v-model="activeTab" stretch>
          <!-- 登录 -->
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top" @submit.prevent="handleLogin">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="loginForm.username" placeholder="请输入用户名" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" native-type="submit" size="large" style="width: 100%">
                  登 录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 注册 -->
          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top" @submit.prevent="handleRegister">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="registerForm.username" placeholder="3-100 个字符" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="registerForm.email" placeholder="请输入邮箱" prefix-icon="Message" size="large" />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-form-item label="显示名称">
                <el-input v-model="registerForm.display_name" placeholder="可选" size="large" />
              </el-form-item>
              <el-form-item label="角色" prop="role">
                <el-select v-model="registerForm.role" size="large" style="width: 100%">
                  <el-option label="管理员 (全权限)" value="admin" />
                  <el-option label="分析师 (读写)" value="analyst" />
                  <el-option label="观察者 (只读)" value="viewer" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" native-type="submit" size="large" style="width: 100%">
                  注 册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="login-footer">
          <span>自动化竞品分析与市场情报系统 v0.1.0</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// ---- 登录 ----
const loginForm = reactive({ username: '', password: '' })
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err: any) {
    const msg = err.response?.data?.detail || '登录失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---- 注册 ----
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  display_name: '',
  role: 'analyst',
})

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 100, message: '3-100 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: (err?: Error) => void) => {
        if (value !== registerForm.password) {
          callback(new Error('两次密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      display_name: registerForm.display_name || undefined,
      role: registerForm.role,
    })
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (err: any) {
    const msg = err.response?.data?.detail || '注册失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  background: #f5f7fa;
}

/* 左侧品牌区 */
.brand-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.brand-side::before {
  content: '';
  position: absolute;
  top: -100px;
  right: -100px;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}

.brand-side::after {
  content: '';
  position: absolute;
  bottom: -80px;
  left: -60px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 460px;
}

.brand-logo {
  margin-bottom: 24px;
}

.brand-title {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: white;
  line-height: 1.4;
  letter-spacing: 1px;
}

.brand-desc {
  margin: 12px 0 40px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 0.5px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.feature-item .el-icon {
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
}

.feature-name {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
}

.feature-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

/* 右侧登录区 */
.form-side {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.login-card {
  width: 100%;
  max-width: 380px;
}

.login-header {
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #1a1a1a;
}

.login-header p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #909399;
}

.login-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
}

/* 响应式：窄屏隐藏左侧 */
@media (max-width: 900px) {
  .brand-side {
    display: none;
  }
  .form-side {
    width: 100%;
  }
  .login-page {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
}
</style>
