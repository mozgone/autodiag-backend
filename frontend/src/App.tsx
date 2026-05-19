import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Managers from './pages/Managers';
import ManagerDetail from './pages/ManagerDetail';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import TelegramApp from './pages/TelegramApp';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuth = useAuthStore((s) => s.isAuthenticated());
  return isAuth ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Публичные маршруты */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Telegram Mini App — особый маршрут, своя авторизация */}
      <Route path="/tg" element={<TelegramApp />} />

      {/* Защищённые маршруты веб-приложения */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="managers" element={<Managers />} />
        <Route path="managers/:id" element={<ManagerDetail />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
