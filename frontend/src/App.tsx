import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import ProtectedRoute from '@/components/ProtectedRoute';
import LoginPage from '@/pages/auth/login';
import RegisterPage from '@/pages/auth/register';
import OTPLoginPage from '@/pages/auth/otp-login';
import QRLoginPage from '@/pages/auth/qr-login';
import Dashboard from '@/pages/Dashboard';

import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* 根路径重定向到仪表板 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 认证相关路由 */}
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/auth/otp-login" element={<OTPLoginPage />} />
        <Route path="/auth/qr-login" element={<QRLoginPage />} />
        
        {/* 受保护的路由 */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        
        {/* 404 页面 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
