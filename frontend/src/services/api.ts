import type { 
  ApiResponse, 
  PaginatedResponse 
} from '@/types/api';

// API 配置
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

// 创建带超时的 fetch 函数
const fetchWithTimeout = (url: string, options: RequestInit = {}, timeout = API_CONFIG.timeout): Promise<Response> => {
  return Promise.race([
    fetch(url, options),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('请求超时')), timeout)
    )
  ]);
};

// 构建完整 URL
const buildUrl = (endpoint: string, params?: Record<string, any>): string => {
  const url = new URL(endpoint, API_CONFIG.baseURL);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
};

// 创建请求头
const createHeaders = (additionalHeaders?: Record<string, string>): HeadersInit => {
  const headers: Record<string, string> = { ...API_CONFIG.headers };
  
  const token = localStorage.getItem('access_token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return { ...headers, ...additionalHeaders };
};

// 处理响应
const handleResponse = async <T>(response: Response): Promise<T> => {
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');
  
  let data: any;
  if (isJson) {
    data = await response.json();
  } else {
    data = await response.text();
  }
  
  if (!response.ok) {
    const error = new Error(data?.message || `HTTP ${response.status}: ${response.statusText}`);
    (error as any).status = response.status;
    (error as any).response = { data, status: response.status };
    throw error;
  }
  
  return data;
};

// 处理 401 错误和 token 刷新
const handleAuthError = async <T>(
  originalRequest: () => Promise<T>,
  url: string
): Promise<T> => {
  // 如果是登录或刷新请求，直接抛出错误
  if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
    throw new Error('认证失败');
  }

  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('没有刷新令牌');
    }

    const refreshResponse = await fetchWithTimeout(
      buildUrl('/api/v1/auth/refresh'),
      {
        method: 'POST',
        headers: createHeaders(),
        body: JSON.stringify({ refresh_token: refreshToken }),
      }
    );

    const refreshData: ApiResponse<{ access_token: string; refresh_token: string }> = 
      await handleResponse(refreshResponse);

    const { access_token, refresh_token: newRefreshToken } = refreshData.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', newRefreshToken);

    // 重试原请求
    return await originalRequest();
  } catch (refreshError) {
    // 刷新失败，清除token并跳转登录
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/auth/login';
    throw refreshError;
  }
};

// 基础请求方法
const request = async <T>(
  method: string,
  endpoint: string,
  options: {
    data?: any;
    params?: Record<string, any>;
    headers?: Record<string, string>;
  } = {}
): Promise<T> => {
  const { data, params, headers } = options;
  
  const makeRequest = async (): Promise<T> => {
    const url = buildUrl(endpoint, params);
    const requestOptions: RequestInit = {
      method,
      headers: createHeaders(headers),
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      requestOptions.body = JSON.stringify(data);
    }

    const response = await fetchWithTimeout(url, requestOptions);
    return handleResponse<T>(response);
  };

  try {
    return await makeRequest();
  } catch (error: any) {
    // 如果是 401 错误，尝试刷新 token 并重试
    if (error.status === 401) {
      return await handleAuthError(makeRequest, endpoint);
    }
    throw error;
  }
};

// 通用请求方法
export const apiRequest = {
  get: <T>(url: string, params?: any): Promise<ApiResponse<T>> =>
    request<ApiResponse<T>>('GET', url, { params }),

  post: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    request<ApiResponse<T>>('POST', url, { data }),

  put: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    request<ApiResponse<T>>('PUT', url, { data }),

  delete: <T>(url: string): Promise<ApiResponse<T>> =>
    request<ApiResponse<T>>('DELETE', url),

  paginated: <T>(url: string, params?: any): Promise<PaginatedResponse<T>> =>
    request<PaginatedResponse<T>>('GET', url, { params }),
};

// 为了向后兼容，导出一个模拟 axios 实例的对象
const api = {
  get: <T>(url: string, config?: { params?: any }): Promise<{ data: ApiResponse<T> }> =>
    request<ApiResponse<T>>('GET', url, { params: config?.params }).then(data => ({ data })),
    
  post: <T>(url: string, data?: any): Promise<{ data: ApiResponse<T> }> =>
    request<ApiResponse<T>>('POST', url, { data }).then(data => ({ data })),
    
  put: <T>(url: string, data?: any): Promise<{ data: ApiResponse<T> }> =>
    request<ApiResponse<T>>('PUT', url, { data }).then(data => ({ data })),
    
  delete: <T>(url: string): Promise<{ data: ApiResponse<T> }> =>
    request<ApiResponse<T>>('DELETE', url).then(data => ({ data })),
};

export default api;
