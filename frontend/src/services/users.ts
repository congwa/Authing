import { apiRequest } from './api';
import type {
  UserResponse,
  UserCreate,
  UserUpdate,
  ChangePasswordRequest,
  UserPoolResponse,
  UserPoolCreate,
  UserPoolUpdate,
  ApplicationResponse,
  ApplicationCreate,
  RoleResponse,
  RoleCreate,
  RoleUpdate,
  PermissionResponse,
  PermissionCreate,
  PermissionUpdate,
  RolePermissionRequest,
  UserRoleRequest,
} from '@/types/api';

export const userService = {
  // 用户池管理
  createUserPool: (data: UserPoolCreate) =>
    apiRequest.post<UserPoolResponse>('/api/v1/users/pools', data),

  listUserPools: (params?: { status?: string; page?: number; per_page?: number }) =>
    apiRequest.paginated<UserPoolResponse>('/api/v1/users/pools', params),

  getUserPool: (poolId: number) =>
    apiRequest.get<UserPoolResponse>(`/api/v1/users/pools/${poolId}`),

  updateUserPool: (poolId: number, data: UserPoolUpdate) =>
    apiRequest.put<UserPoolResponse>(`/api/v1/users/pools/${poolId}`, data),

  // 应用管理
  createApplication: (data: ApplicationCreate) =>
    apiRequest.post<ApplicationResponse>('/api/v1/users/applications', data),

  // 用户管理
  createUser: (data: UserCreate) =>
    apiRequest.post<UserResponse>('/api/v1/users/', data),

  listUsers: (params: { 
    user_pool_id: number; 
    status?: string; 
    search?: string;
    page?: number; 
    per_page?: number; 
  }) =>
    apiRequest.paginated<UserResponse>('/api/v1/users/', params),

  getUser: (userId: number) =>
    apiRequest.get<UserResponse>(`/api/v1/users/${userId}`),

  updateUser: (userId: number, data: UserUpdate) =>
    apiRequest.put<UserResponse>(`/api/v1/users/${userId}`, data),

  deleteUser: (userId: number) =>
    apiRequest.delete<boolean>(`/api/v1/users/${userId}`),

  changePassword: (userId: number, data: ChangePasswordRequest) =>
    apiRequest.post<boolean>(`/api/v1/users/${userId}/change-password`, data),

  resetPassword: (userId: number, newPassword: string) =>
    apiRequest.post<boolean>(`/api/v1/users/${userId}/reset-password`, { new_password: newPassword }),
};

export const rbacService = {
  // 角色管理
  createRole: (data: RoleCreate) =>
    apiRequest.post<RoleResponse>('/api/v1/rbac/roles', data),

  listRoles: (params: { user_pool_id: number; page?: number; per_page?: number }) =>
    apiRequest.get<{ roles: RoleResponse[]; total: number }>('/api/v1/rbac/roles', params),

  getRole: (roleId: number) =>
    apiRequest.get<RoleResponse>(`/api/v1/rbac/roles/${roleId}`),

  updateRole: (roleId: number, data: RoleUpdate) =>
    apiRequest.put<RoleResponse>(`/api/v1/rbac/roles/${roleId}`, data),

  deleteRole: (roleId: number) =>
    apiRequest.delete<boolean>(`/api/v1/rbac/roles/${roleId}`),

  // 权限管理
  createPermission: (data: PermissionCreate) =>
    apiRequest.post<PermissionResponse>('/api/v1/rbac/permissions', data),

  listPermissions: (params: { user_pool_id: number; page?: number; per_page?: number }) =>
    apiRequest.get<{ permissions: PermissionResponse[]; total: number }>('/api/v1/rbac/permissions', params),

  getPermission: (permissionId: number) =>
    apiRequest.get<PermissionResponse>(`/api/v1/rbac/permissions/${permissionId}`),

  updatePermission: (permissionId: number, data: PermissionUpdate) =>
    apiRequest.put<PermissionResponse>(`/api/v1/rbac/permissions/${permissionId}`, data),

  deletePermission: (permissionId: number) =>
    apiRequest.delete<boolean>(`/api/v1/rbac/permissions/${permissionId}`),

  // 角色权限关联
  assignPermissionsToRole: (roleId: number, data: RolePermissionRequest) =>
    apiRequest.post<boolean>(`/api/v1/rbac/roles/${roleId}/permissions`, data),

  getRolePermissions: (roleId: number) =>
    apiRequest.get<PermissionResponse[]>(`/api/v1/rbac/roles/${roleId}/permissions`),

  removePermissionsFromRole: (roleId: number, permissionIds: number[]) =>
    apiRequest.delete<boolean>(`/api/v1/rbac/roles/${roleId}/permissions/${permissionIds.join(',')}`),

  // 用户角色分配
  assignRolesToUser: (userId: number, data: UserRoleRequest) =>
    apiRequest.post<boolean>(`/api/v1/rbac/users/${userId}/roles`, data),

  getUserRoles: (userId: number) =>
    apiRequest.get<RoleResponse[]>(`/api/v1/rbac/users/${userId}/roles`),

  removeRolesFromUser: (userId: number, roleIds: number[]) =>
    apiRequest.delete<boolean>(`/api/v1/rbac/users/${userId}/roles/${roleIds.join(',')}`),
};
