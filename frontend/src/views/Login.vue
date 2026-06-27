<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>竞品分析系统</h1>
        <p>Competitive Intelligence Platform</p>
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
                登录
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
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
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
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  padding: 40px 36px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h1 {
  margin: 0;
  font-size: 26px;
  color: #303133;
}

.login-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #909399;
}
</style>
