<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-title">
        <el-icon size="28" color="#409eff"><Tools /></el-icon>
        <h2>ForkliftCLI 后台管理系统</h2>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="onLogin"
      >
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入管理员手机号" size="large">
            <template #prefix><el-icon><Iphone /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="onLogin"
        >
          登 录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ phone: '', password: '' })
const rules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onLogin() {
  await formRef.value?.validate()
  loading.value = true
  try {
    await auth.login(form.phone, form.password)
    ElMessage.success('登录成功')
    router.push((route.query.redirect as string) || '/dashboard')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #409eff 100%);
}
.login-card {
  width: 400px;
  padding: 24px 16px;
  border-radius: 8px;
}
.login-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 24px;
}
.login-title h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
.login-btn {
  width: 100%;
}
</style>
