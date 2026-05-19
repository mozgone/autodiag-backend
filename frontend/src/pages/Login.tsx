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
      minHeight: '100vh', background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, padding: '40px', width: '100%', maxWidth: 400,
        boxShadow: '0 25px 50px rgba(0,0,0,0.3)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <div style={{ background: '#6366f1', borderRadius: 16, padding: 14 }}>
              <TrendingUp size={32} color="#fff" />
            </div>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#1e293b', marginBottom: 4 }}>Sellex</h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>Войдите в систему</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#374151', marginBottom: 6 }}>Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
              style={{ width: '100%', padding: '12px 14px', border: '1.5px solid #e2e8f0', borderRadius: 10, fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
              onFocus={(e) => (e.target.style.borderColor = '#6366f1')}
              onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#374151', marginBottom: 6 }}>Пароль</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
              style={{ width: '100%', padding: '12px 14px', border: '1.5px solid #e2e8f0', borderRadius: 10, fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
              onFocus={(e) => (e.target.style.borderColor = '#6366f1')}
              onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
            />
          </div>
          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '13px', background: loading ? '#a5b4fc' : '#6366f1',
              color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600,
              transition: 'background 0.15s',
            }}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div style={{ marginTop: 24, padding: 16, background: '#f8fafc', borderRadius: 10, fontSize: 13, color: '#64748b' }}>
          <strong>Демо-доступ:</strong><br />
          Email: admin@sellex.demo<br />
          Пароль: demo1234
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: '#64748b' }}>
          Нет аккаунта?{' '}
          <Link to="/register" style={{ color: '#6366f1', fontWeight: 600, textDecoration: 'none' }}>
            Зарегистрировать компанию
          </Link>
        </p>
      </div>
    </div>
  );
}
