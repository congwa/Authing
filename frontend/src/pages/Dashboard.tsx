import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, User, Settings, Shield, Users } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Authing</h1>
              <span className="ml-2 text-sm text-gray-500">管理控制台</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-700">
                  {user?.nickname || user?.username || '用户'}
                </span>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2" />
                退出登录
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* 欢迎信息 */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">
            欢迎回来，{user?.nickname || user?.username}！
          </h2>
          <p className="mt-2 text-gray-600">
            管理您的身份认证、用户和权限设置
          </p>
        </div>

        {/* 用户信息卡片 */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle>用户信息</CardTitle>
              <CardDescription>您的账户详细信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">用户名</label>
                  <p className="text-gray-900">{user?.username || '未设置'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">昵称</label>
                  <p className="text-gray-900">{user?.nickname || '未设置'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">邮箱</label>
                  <p className="text-gray-900">
                    {user?.email || '未设置'}
                    {user?.email && (
                      <span className={`ml-2 text-xs px-2 py-1 rounded ${
                        user.email_verified 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {user.email_verified ? '已验证' : '未验证'}
                      </span>
                    )}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">手机号</label>
                  <p className="text-gray-900">
                    {user?.phone || '未设置'}
                    {user?.phone && (
                      <span className={`ml-2 text-xs px-2 py-1 rounded ${
                        user.phone_verified 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {user.phone_verified ? '已验证' : '未验证'}
                      </span>
                    )}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">用户池ID</label>
                  <p className="text-gray-900">{user?.user_pool_id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">状态</label>
                  <span className={`inline-flex px-2 py-1 text-xs rounded ${
                    user?.status === 'active' 
                      ? 'bg-green-100 text-green-800'
                      : user?.status === 'blocked'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {user?.status === 'active' ? '正常' : 
                     user?.status === 'blocked' ? '已禁用' : '待激活'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 功能卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center">
                <Users className="h-6 w-6 text-blue-600 mr-3" />
                <div>
                  <CardTitle className="text-lg">用户管理</CardTitle>
                  <CardDescription>管理用户账户和信息</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                创建、编辑和管理用户账户，查看用户活动状态
              </p>
              <Button variant="outline" size="sm" disabled>
                即将上线
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center">
                <Shield className="h-6 w-6 text-green-600 mr-3" />
                <div>
                  <CardTitle className="text-lg">权限管理</CardTitle>
                  <CardDescription>配置角色和权限</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                创建角色，分配权限，管理用户的访问控制
              </p>
              <Button variant="outline" size="sm" disabled>
                即将上线
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center">
                <Settings className="h-6 w-6 text-purple-600 mr-3" />
                <div>
                  <CardTitle className="text-lg">系统设置</CardTitle>
                  <CardDescription>配置应用和安全设置</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                配置用户池设置，管理应用集成和安全策略
              </p>
              <Button variant="outline" size="sm" disabled>
                即将上线
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* 最近活动 */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>最近活动</CardTitle>
              <CardDescription>您的最近登录和操作记录</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">成功登录</span>
                  </div>
                  <span className="text-sm text-gray-500">刚刚</span>
                </div>
                
                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm">访问管理控制台</span>
                  </div>
                  <span className="text-sm text-gray-500">刚刚</span>
                </div>

                {user?.last_login_at && (
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                      <span className="text-sm">上次登录</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(user.last_login_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
