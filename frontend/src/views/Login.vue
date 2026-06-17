<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { apiFetch } from '../utils/api';

const router = useRouter();

const form = reactive({
  student_id: '',
  password: ''
});

const showPassword = ref(false);
const loading = ref(false);
const errorMessage = ref('');

const handleSubmit = async () => {
  errorMessage.value = '';
  
  if (!form.student_id.trim()) {
    errorMessage.value = '请输入学号';
    return;
  }
  
  if (!form.password) {
    errorMessage.value = '请输入密码';
    return;
  }
  
  loading.value = true;
  
  try {
    const response = await apiFetch('/api/login/', {
      method: 'POST',
      body: JSON.stringify({
        student_id: form.student_id.trim(),
        password: form.password
      })
    });
    
    const data = await response.json();
    
    if (data.code === 200) {
      localStorage.setItem('token', data.data.token);
      localStorage.setItem('user', JSON.stringify(data.data.user));
      
      const userInfoResponse = await apiFetch('/api/user-info/');
      
      const userInfoData = await userInfoResponse.json();
      if (userInfoData.code === 200) {
        localStorage.setItem('permissions', JSON.stringify(userInfoData.data.permissions || []));
        localStorage.setItem('roleName', userInfoData.data.role_name || '');
      }
      
      router.push('/');
    } else {
      errorMessage.value = data.message || '登录失败';
    }
  } catch (error) {
    errorMessage.value = '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

const handleKeydown = (e) => {
  if (e.key === 'Enter') {
    handleSubmit();
  }
};
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <span class="logo-icon">🎓</span>
          <span class="logo-text">学生会管理系统</span>
        </div>
        <p class="login-title">欢迎登录</p>
        <p class="login-subtitle">请输入您的学号和密码</p>
      </div>
      
      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">
            <span class="label-icon">📋</span>
            <span>学号</span>
          </label>
          <input
            v-model="form.student_id"
            type="text"
            class="form-input"
            placeholder="请输入学号"
            @keydown="handleKeydown"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="label-icon">🔑</span>
            <span>密码</span>
          </label>
          <div class="password-input-wrapper">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input password-input"
              placeholder="请输入密码"
              @keydown="handleKeydown"
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>
        
        <div v-if="errorMessage" class="error-message">
          <span class="error-icon">⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>
        
        <button
          type="submit"
          class="login-btn"
          :disabled="loading"
        >
          <span v-if="loading" class="loading-spinner">⏳</span>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>
      
      <div class="login-footer">
        <p>忘记密码？请联系管理员</p>
        <p class="security-tip">
          <span class="tip-icon">🛡️</span>
          系统采用加密传输，保障您的信息安全
        </p>
      </div>
    </div>
    
    <div class="login-background">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  background: #ffffff;
  top: -200px;
  right: -100px;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  background: #ffffff;
  bottom: -150px;
  left: -100px;
}

.bg-circle-3 {
  width: 300px;
  height: 300px;
  background: #ffffff;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 32px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  font-family: 'Microsoft YaHei', sans-serif;
}

.login-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: #999999;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
}

.label-icon {
  font-size: 16px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input::placeholder {
  color: #cccccc;
}

.password-input-wrapper {
  position: relative;
}

.password-input {
  padding-right: 48px;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.password-toggle:hover {
  background: #f5f5f5;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  color: #d93026;
  font-size: 13px;
}

.error-icon {
  font-size: 14px;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.login-footer p {
  margin: 8px 0;
  font-size: 13px;
  color: #999999;
}

.security-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tip-icon {
  font-size: 14px;
}
</style>