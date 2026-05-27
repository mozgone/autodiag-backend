import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { login } from '../api/client';
import { useAuthStore } from '../store/auth';

export default function Login() {
  const [email, setEmail] = useState('admin@sellex.demo');
  const [password, setPassword] = useState('demo1234');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await login(email, password);
      setAuth(data.access_token, {
        id: data.user_id, tenant_id: data.tenant_id, role: data.role,
        full_name: data.full_name, email, is_active: true,
      });
      navigate('/dashboard');
    } catch {
      toast.error('Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#0f0f1a',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: '#1a1a2e', borderRadius: 20, padding: '40px', width: '100%', maxWidth: 400,
        boxShadow: '0 25px 60px rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.07)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <div style={{ background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)', borderRadius: 16, padding: 14 }}>
              <TrendingUp size={32} color="#fff" />
            </div>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>Sellex</h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>Войдите в систему</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#94a3b8', marginBottom: 6 }}>Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
              style={{ width: '100%', padding: '12px 14px', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: 10, fontSize: 14, outline: 'none', transition: 'border 0.15s', background: 'rgba(255,255,255,0.04)', color: '#f1f5f9' }}
              onFocus={(e) => (e.target.style.borderColor = '#2dd4bf')}
              onBlur={(e) => (e.target.style.borderColor = 'rgba(255,255,255,0.1)')}
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#94a3b8', marginBottom: 6 }}>Пароль</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
              style={{ width: '100%', padding: '12px 14px', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: 10, fontSize: 14, outline: 'none', transition: 'border 0.15s', background: 'rgba(255,255,255,0.04)', color: '#f1f5f9' }}
              onFocus={(e) => (e.target.style.borderColor = '#2dd4bf')}
              onBlur={(e) => (e.target.style.borderColor = 'rgba(255,255,255,0.1)')}
            />
          </div>
          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '13px', background: loading ? 'rgba(45,212,191,0.5)' : 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)',
              color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer', transition: 'opacity 0.15s',
            }}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div style={{ marginTop: 24, padding: 16, background: 'rgba(255,255,255,0.04)', borderRadius: 10, fontSize: 13, color: '#64748b', border: '1px solid rgba(255,255,255,0.07)' }}>
          <strong style={{ color: '#94a3b8' }}>Демо-доступ:</strong><br />
          Email: admin@sellex.demo<br />
          Пароль: demo1234
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: '#64748b' }}>
          Нет аккаунта?{' '}
          <Link to="/register" style={{ color: '#2dd4bf', fontWeight: 600, textDecoration: 'none' }}>
            Зарегистрировать компанию
          </Link>
        </p>
      </div>
    </div>
  );
}
