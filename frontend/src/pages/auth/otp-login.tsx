import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/stores/auth';

const sendOTPSchema = z.object({
  identifier: z.string().min(1, '请输入手机号或邮箱'),
  userPoolId: z.number().default(parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1')),
});

const verifyOTPSchema = z.object({
  code: z.string().length(6, '验证码为6位数字'),
});

type SendOTPFormData = z.infer<typeof sendOTPSchema>;
type VerifyOTPFormData = z.infer<typeof verifyOTPSchema>;

const OTPLoginPage: React.FC = () => {
  const [step, setStep] = useState<'send' | 'verify'>('send');
  const [identifier, setIdentifier] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();

  const sendForm = useForm<SendOTPFormData>({
    resolver: zodResolver(sendOTPSchema),
    defaultValues: {
      identifier: '',
      userPoolId: parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1'),
    },
  });

  const verifyForm = useForm<VerifyOTPFormData>({
    resolver: zodResolver(verifyOTPSchema),
    defaultValues: {
      code: '',
    },
  });

  // 倒计时效果
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const onSendOTP = async (data: SendOTPFormData) => {
    try {
      setIsLoading(true);
      await authService.sendOTP({
        identifier: data.identifier,
        type: 'login',
        user_pool_id: data.userPoolId,
      });
      
      setIdentifier(data.identifier);
      setStep('verify');
      setCountdown(60);
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || '发送验证码失败，请稍后重试';
      sendForm.setError('root', { message: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const onVerifyOTP = async (data: VerifyOTPFormData) => {
    try {
      setIsLoading(true);
      const response = await authService.otpLogin({
        identifier,
        code: data.code,
        type: 'login',
        user_pool_id: parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1'),
      });

      const { access_token, refresh_token, user } = response.data;
      setTokens({ access_token, refresh_token, user });
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || '验证码错误或已过期';
      verifyForm.setError('root', { message: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const resendOTP = async () => {
    try {
      setIsLoading(true);
      await authService.sendOTP({
        identifier,
        type: 'login',
        user_pool_id: parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1'),
      });
      setCountdown(60);
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || '重发验证码失败';
      verifyForm.setError('root', { message: errorMessage });
    } finally {
      setIsLoading(false);
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
            <div className="flex items-center">
              {step === 'verify' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStep('send')}
                  className="mr-2 p-1"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <div className="flex-1">
                <CardTitle className="text-2xl font-bold text-center">
                  {step === 'send' ? '短信登录' : '验证码登录'}
                </CardTitle>
                <CardDescription className="text-center">
                  {step === 'send' 
                    ? '使用手机号或邮箱获取验证码登录'
                    : `验证码已发送至 ${identifier.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')}`
                  }
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {step === 'send' ? (
              <Form {...sendForm}>
                <form onSubmit={sendForm.handleSubmit(onSendOTP)} className="space-y-4">
                  <FormField
                    control={sendForm.control}
                    name="identifier"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>手机号或邮箱</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="请输入手机号或邮箱"
                            {...field}
                            disabled={isLoading}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {sendForm.formState.errors.root && (
                    <div className="text-sm text-red-600 text-center">
                      {sendForm.formState.errors.root.message}
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
                        发送中...
                      </>
                    ) : (
                      '获取验证码'
                    )}
                  </Button>
                </form>
              </Form>
            ) : (
              <Form {...verifyForm}>
                <form onSubmit={verifyForm.handleSubmit(onVerifyOTP)} className="space-y-4">
                  <FormField
                    control={verifyForm.control}
                    name="code"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>验证码</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="请输入6位验证码"
                            maxLength={6}
                            {...field}
                            disabled={isLoading}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">
                      {countdown > 0 ? `${countdown}秒后可重发` : ''}
                    </span>
                    <Button
                      type="button"
                      variant="link"
                      className="p-0 h-auto"
                      disabled={countdown > 0 || isLoading}
                      onClick={resendOTP}
                    >
                      重新发送
                    </Button>
                  </div>

                  {verifyForm.formState.errors.root && (
                    <div className="text-sm text-red-600 text-center">
                      {verifyForm.formState.errors.root.message}
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
                        验证中...
                      </>
                    ) : (
                      '登录'
                    )}
                  </Button>
                </form>
              </Form>
            )}
          </CardContent>

          <CardFooter className="text-center">
            <div className="w-full">
              <span className="text-sm text-gray-600">
                其他登录方式：{' '}
                <Link
                  to="/auth/login"
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  密码登录
                </Link>
                {' | '}
                <Link
                  to="/auth/qr-login"
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  扫码登录
                </Link>
              </span>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default OTPLoginPage;
