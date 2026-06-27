import api from './index'
import type { User, UserRegister, UserLogin, TokenResponse } from '@/types'

export const authApi = {
  register(data: UserRegister) {
    return api.post<User>('/auth/register', data)
  },

  login(data: UserLogin) {
    return api.post<TokenResponse>('/auth/login', data)
  },

  refreshToken(refresh_token: string) {
    return api.post<TokenResponse>('/auth/refresh', { refresh_token })
  },

  getMe() {
    return api.get<User>('/auth/me')
  },

  changePassword(oldPassword: string, newPassword: string) {
    return api.put('/auth/change-password', null, {
      params: { old_password: oldPassword, new_password: newPassword },
    })
  },
}
