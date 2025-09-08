// 通用API响应类型
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

export interface PaginatedResponse<T = any> {
  code: number;
  message: string;
  data: T[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  timestamp: string;
}

export interface ErrorResponse {
  code: number;
  message: string;
  errors?: Array<{
    field: string;
    message: string;
  }>;
  timestamp: string;
}

// 认证相关类型
export interface LoginRequest {
  identifier: string;
  password: string;
  user_pool_id: number;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  phone?: string;
  nickname?: string;
  user_pool_id: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface SendOTPRequest {
  identifier: string;
  type: 'login' | 'register' | 'reset_password' | 'verify';
  user_pool_id: number;
}

export interface OTPLoginRequest {
  identifier: string;
  code: string;
  type: 'login' | 'register' | 'reset_password' | 'verify';
  user_pool_id: number;
}

export interface QRLoginCreateResponse {
  scene_id: string;
  qr_url: string;
  expires_at: string;
}

export interface QRLoginStatusResponse {
  status: 'pending' | 'scanned' | 'confirmed' | 'expired' | 'cancelled';
  user?: UserResponse;
  token?: TokenResponse;
}

export interface QRLoginConfirmRequest {
  user_pool_id: number;
}

export interface ResetPasswordRequest {
  identifier: string;
  code: string;
  new_password: string;
  user_pool_id: number;
}

// 用户相关类型
export interface UserResponse {
  id: number;
  user_pool_id: number;
  username?: string;
  email?: string;
  phone?: string;
  nickname?: string;
  avatar_url?: string;
  profile_data?: Record<string, any>;
  email_verified: boolean;
  phone_verified: boolean;
  status: 'active' | 'blocked' | 'pending';
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username?: string;
  password: string;
  email?: string;
  phone?: string;
  nickname?: string;
  user_pool_id: number;
  profile_data?: Record<string, any>;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  phone?: string;
  nickname?: string;
  avatar_url?: string;
  profile_data?: Record<string, any>;
  status?: 'active' | 'blocked' | 'pending';
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// 用户池相关类型
export interface UserPoolResponse {
  id: number;
  name: string;
  description?: string;
  settings?: Record<string, any>;
  status: 'active' | 'disabled';
  created_at: string;
  updated_at: string;
}

export interface UserPoolCreate {
  name: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface UserPoolUpdate {
  name?: string;
  description?: string;
  settings?: Record<string, any>;
  status?: 'active' | 'disabled';
}

// 应用相关类型
export interface ApplicationResponse {
  id: number;
  user_pool_id: number;
  app_name: string;
  app_id: string;
  callback_urls?: string[];
  logout_urls?: string[];
  allowed_origins?: string[];
  token_lifetime: number;
  refresh_token_lifetime: number;
  status: 'active' | 'disabled';
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  user_pool_id: number;
  app_name: string;
  callback_urls?: string[];
  logout_urls?: string[];
  allowed_origins?: string[];
  token_lifetime?: number;
  refresh_token_lifetime?: number;
}

// 角色和权限相关类型
export interface RoleResponse {
  id: number;
  user_pool_id: number;
  role_name: string;
  role_code: string;
  description?: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  user_pool_id: number;
  role_name: string;
  role_code: string;
  description?: string;
}

export interface RoleUpdate {
  role_name?: string;
  role_code?: string;
  description?: string;
}

export interface PermissionResponse {
  id: number;
  user_pool_id: number;
  permission_name: string;
  permission_code: string;
  resource: string;
  action: string;
  description?: string;
  created_at: string;
}

export interface PermissionCreate {
  user_pool_id: number;
  permission_name: string;
  permission_code: string;
  resource: string;
  action: string;
  description?: string;
}

export interface PermissionUpdate {
  permission_name?: string;
  permission_code?: string;
  resource?: string;
  action?: string;
  description?: string;
}

export interface RolePermissionRequest {
  permission_ids: number[];
}

export interface UserRoleRequest {
  role_ids: number[];
  expires_at?: string;
}
