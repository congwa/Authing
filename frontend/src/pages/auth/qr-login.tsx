import React, { useState, useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Loader2, RefreshCw, CheckCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/stores/auth';

type QRStatus = 'pending' | 'scanned' | 'confirmed' | 'expired' | 'cancelled' | 'loading';

const QRLoginPage: React.FC = () => {
  const [qrData, setQrData] = useState<{ scene_id: string; qr_url: string; expires_at: string } | null>(null);
  const [status, setStatus] = useState<QRStatus>('loading');
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const userPoolId = parseInt(import.meta.env.VITE_DEFAULT_USER_POOL_ID || '1');
  const appId = 'default-app'; // 默认应用ID

  // 创建二维码
  const createQR = async () => {
    try {
      setIsCreating(true);
      const response = await authService.createQRLogin(userPoolId, appId);
      setQrData(response.data);
      setStatus('pending');
      startPolling(response.data.scene_id);
    } catch (error: any) {
      console.error('创建二维码失败:', error);
      setStatus('expired');
    } finally {
      setIsCreating(false);
    }
  };

  // 开始轮询状态
  const startPolling = (sceneId: string) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(async () => {
      try {
        const response = await authService.getQRLoginStatus(sceneId);
        const { status: qrStatus, user, token } = response.data;
        
        setStatus(qrStatus);

        if (qrStatus === 'confirmed' && token) {
          // 登录成功
          const { access_token, refresh_token } = token;
          setTokens({ access_token, refresh_token, user: user! });
          stopPolling();
          navigate('/dashboard');
        } else if (qrStatus === 'expired' || qrStatus === 'cancelled') {
          // 二维码过期或取消
          stopPolling();
        }
      } catch (error) {
        console.error('获取二维码状态失败:', error);
        stopPolling();
        setStatus('expired');
      }
    }, 2000); // 每2秒轮询一次
  };

  // 停止轮询
  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // 组件挂载时创建二维码
  useEffect(() => {
    createQR();
    
    // 组件卸载时清理
    return () => {
      stopPolling();
    };
  }, []);

  // 刷新二维码
  const refreshQR = () => {
    stopPolling();
    setQrData(null);
    setStatus('loading');
    createQR();
  };

  const getStatusText = () => {
    switch (status) {
      case 'loading':
        return '生成二维码中...';
      case 'pending':
        return '请使用移动设备扫描二维码';
      case 'scanned':
        return '扫描成功，请在移动设备上确认登录';
      case 'confirmed':
        return '登录成功，正在跳转...';
      case 'expired':
        return '二维码已过期，请刷新重试';
      case 'cancelled':
        return '登录已取消';
      default:
        return '';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'loading':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />;
      case 'scanned':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'confirmed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'expired':
      case 'cancelled':
        return <RefreshCw className="h-5 w-5 text-gray-400" />;
      default:
        return null;
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
            <CardTitle className="text-2xl font-bold text-center">扫码登录</CardTitle>
            <CardDescription className="text-center">
              使用手机应用扫描二维码快速登录
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="flex flex-col items-center space-y-4">
              {/* 二维码区域 */}
              <div className="relative">
                <div className="w-48 h-48 bg-white border border-gray-200 rounded-lg flex items-center justify-center">
                  {status === 'loading' || isCreating ? (
                    <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                  ) : qrData && (status === 'pending' || status === 'scanned') ? (
                    <QRCodeSVG
                      value={qrData.qr_url}
                      size={180}
                      level="M"
                      includeMargin={true}
                    />
                  ) : (
                    <div className="text-center">
                      <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">二维码已过期</p>
                    </div>
                  )}
                </div>
                
                {/* 状态遮罩 */}
                {(status === 'expired' || status === 'cancelled') && (
                  <div className="absolute inset-0 bg-white bg-opacity-90 rounded-lg flex items-center justify-center">
                    <Button
                      onClick={refreshQR}
                      disabled={isCreating}
                      variant="outline"
                      size="sm"
                    >
                      {isCreating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          生成中...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4" />
                          刷新二维码
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>

              {/* 状态提示 */}
              <div className="flex items-center space-x-2 text-center">
                {getStatusIcon()}
                <span className="text-sm text-gray-600">
                  {getStatusText()}
                </span>
              </div>

              {/* 刷新按钮 */}
              {(status === 'pending' || status === 'scanned') && (
                <Button
                  onClick={refreshQR}
                  disabled={isCreating}
                  variant="outline"
                  size="sm"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  刷新
                </Button>
              )}
            </div>

            {/* 说明文字 */}
            <div className="text-center space-y-2">
              <p className="text-xs text-gray-500">
                打开您的移动应用，扫描上方二维码即可快速登录
              </p>
              <p className="text-xs text-gray-400">
                二维码有效期为2分钟
              </p>
            </div>
          </CardContent>

          <CardFooter className="text-center">
            <div className="w-full space-y-3">
              <div className="text-sm text-gray-600">
                其他登录方式：
              </div>
              <div className="flex justify-center space-x-4 text-sm">
                <Link
                  to="/auth/login"
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  密码登录
                </Link>
                <Link
                  to="/auth/otp-login"
                  className="text-blue-600 hover:text-blue-500 font-medium"
                >
                  短信登录
                </Link>
              </div>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default QRLoginPage;
