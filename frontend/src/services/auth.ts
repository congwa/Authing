import { apiRequest } from './api';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RefreshTokenRequest,
  SendOTPRequest,
  OTPLoginRequest,
  QRLoginCreateResponse,
  QRLoginStatusResponse,
  QRLoginConfirmRequest,
  ResetPasswordRequest,
  UserResponse,
} from '@/types/api';

export const authService = {
  // 用户名密码登录
  login: (data: LoginRequest) =>
    apiRequest.post<TokenResponse>('/api/v1/auth/login', data),

  // 用户注册
  register: (data: RegisterRequest) =>
    apiRequest.post<TokenResponse>('/api/v1/auth/register', data),

  // 刷新Token
  refreshToken: (data: RefreshTokenRequest) =>
    apiRequest.post<TokenResponse>('/api/v1/auth/refresh', data),

  // 用户登出
  logout: () =>
    apiRequest.post<boolean>('/api/v1/auth/logout'),

  // 发送OTP验证码
  sendOTP: (data: SendOTPRequest) =>
    apiRequest.post<boolean>('/api/v1/auth/otp/send', data),

  // OTP验证码登录
  otpLogin: (data: OTPLoginRequest) =>
    apiRequest.post<TokenResponse>('/api/v1/auth/otp/login', data),

  // 创建扫码登录
  createQRLogin: (user_pool_id: number, app_id: string) =>
    apiRequest.get<QRLoginCreateResponse>('/api/v1/auth/qr/create', { user_pool_id, app_id }),

  // 获取扫码登录状态
  getQRLoginStatus: (scene_id: string) =>
    apiRequest.get<QRLoginStatusResponse>(`/api/v1/auth/qr/${scene_id}/status`),

  // 确认扫码登录
  confirmQRLogin: (scene_id: string, data: QRLoginConfirmRequest) =>
    apiRequest.post<boolean>(`/api/v1/auth/qr/${scene_id}/confirm`, data),

  // 重置密码
  resetPassword: (data: ResetPasswordRequest) =>
    apiRequest.post<boolean>('/api/v1/auth/reset-password', data),

  // 获取当前用户信息
  getCurrentUser: () =>
    apiRequest.get<UserResponse>('/api/v1/users/me'),
};
