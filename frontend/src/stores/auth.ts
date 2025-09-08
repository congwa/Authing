import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '@/types/api';
import { authService } from '@/services/auth';

interface AuthState {
  // 状态
  user: UserResponse | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // 操作方法
  login: (identifier: string, password: string, userPoolId: number) => Promise<void>;
  register: (userData: {
    username: string;
    password: string;
    email?: string;
    phone?: string;
    nickname?: string;
    userPoolId: number;
  }) => Promise<void>;
  logout: () => void;
  setTokens: (tokens: { access_token: string; refresh_token: string; user: UserResponse }) => void;
  clearAuth: () => void;
  refreshUserInfo: () => Promise<void>;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      // 登录方法
      login: async (identifier: string, password: string, userPoolId: number) => {
        try {
          set({ isLoading: true });
          
          const response = await authService.login({
            identifier,
            password,
            user_pool_id: userPoolId,
          });

          const { access_token, refresh_token, user } = response.data;

          // 存储到localStorage
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      // 注册方法
      register: async (userData) => {
        try {
          set({ isLoading: true });
          
          const response = await authService.register({
            username: userData.username,
            password: userData.password,
            email: userData.email,
            phone: userData.phone,
            nickname: userData.nickname,
            user_pool_id: userData.userPoolId,
          });

          const { access_token, refresh_token, user } = response.data;

          // 存储到localStorage
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      // 登出方法
      logout: () => {
        try {
          authService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // 清除本地存储
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      // 设置tokens
      setTokens: (tokens) => {
        const { access_token, refresh_token, user } = tokens;
        
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        });
      },

      // 清除认证信息
      clearAuth: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      // 刷新用户信息
      refreshUserInfo: async () => {
        try {
          const response = await authService.getCurrentUser();
          set({ user: response.data });
        } catch (error) {
          console.error('Failed to refresh user info:', error);
          // 如果获取用户信息失败，可能token已过期，清除认证状态
          get().clearAuth();
        }
      },

      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
