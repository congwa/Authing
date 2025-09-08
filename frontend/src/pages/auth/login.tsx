import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { useAuthStore } from '@/stores/auth';

const loginSchema = z.object({
  identifier: z.string().min(1, '请输入用户名/邮箱/手机号'),
  password: z.string().min(6, '密码至少6位'),
  userPoolId: z.number().default(parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1')),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      identifier: '',
      password: '',
      userPoolId: parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1'),
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.identifier, data.password, data.userPoolId);
      navigate('/dashboard');
    } catch (error: any) {
      // 处理登录错误
      const errorMessage = error?.response?.data?.message || '登录失败，请检查用户名和密码';
      form.setError('root', { message: errorMessage });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Authing</h1>
          <p className="mt-2 text-sm text-gray-600">统一身份认证平台</p>
        </div>

        <Card className="w-full">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">登录</CardTitle>
            <CardDescription className="text-center">
              使用您的账户登录到平台
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="identifier"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>用户名/邮箱/手机号</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="请输入用户名、邮箱或手机号"
                          {...field}
                          disabled={isLoading}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>密码</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="请输入密码"
                            {...field}
                            disabled={isLoading}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                            onClick={() => setShowPassword(!showPassword)}
                            disabled={isLoading}
                          >
                            {showPassword ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {form.formState.errors.root && (
                  <div className="text-sm text-red-600 text-center">
                    {form.formState.errors.root.message}
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      登录中...
                    </>
                  ) : (
                    '登录'
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <div className="flex items-center justify-between w-full text-sm">
              <Link
                to="/auth/forgot-password"
                className="text-blue-600 hover:text-blue-500"
              >
                忘记密码？
              </Link>
              <Link
                to="/auth/otp-login"
                className="text-blue-600 hover:text-blue-500"
              >
                短信登录
              </Link>
            </div>
            
            <div className="text-center">
              <span className="text-sm text-gray-600">
                还没有账户？{' '}
                <Link
                  to="/auth/register"
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  立即注册
                </Link>
              </span>
            </div>

            <div className="text-center">
              <Link
                to="/auth/qr-login"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                扫码登录
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
