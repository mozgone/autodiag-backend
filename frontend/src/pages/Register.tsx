import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { TrendingUp, Building2, User, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { register } from '../api/client';
import { useAuthStore } from '../store/auth';

const inputWrap: React.CSSProperties = { position: 'relative', width: '100%' };
const inputBase: React.CSSProperties = {
  width: '100%', padding: '12px 14px 12px 40px',
  border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: 10,
  fontSize: 14, outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
  background: 'rgba(255,255,255,0.04)', color: '#f1f5f9',
};
const iconPos: React.CSSProperties = {
  position: 'absolute', left: 13, top: '50%',
  transform: 'translateY(-50%)', color: '#64748b', pointerEvents: 'none',
};

interface FieldProps {
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  suffix?: React.ReactNode;
}

function Field({ label, icon, value, onChange, type = 'text', placeholder, suffix }: FieldProps) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#94a3b8', marginBottom: 6 }}>
        {label}
      </label>
      <div style={inputWrap}>
        <span style={iconPos}>{icon}</span>
        <input
          type={type} value={value} placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)} required
          style={inputBase}
          onFocus={(e) => (e.target.style.borderColor = '#2dd4bf')}
          onBlur={(e) => (e.target.style.borderColor = 'rgba(255,255,255,0.1)')}
        />
        {suffix && (
          <span style={{ position: 'absolute', right: 13, top: '50%', transform: 'translateY(-50%)' }}>
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

export default function Register() {
  const [companyName, setCompanyName] = useState('');
  const [fullName, setFullName]       = useState('');
  const [email, setEmail]             = useState('');
  const [password, setPassword]       = useState('');
  const [showPwd, setShowPwd]         = useState(false);
  const [loading, setLoading]         = useState(false);
  const navigate  = useNavigate();
  const setAuth   = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) { toast.error('Пароль минимум 6 символов'); return; }
    setLoading(true);
    try {
      const data = await register({ company_name: companyName, full_name: fullName, email, password });
      setAuth(data.access_token, {
        id: data.user_id, tenant_id: data.tenant_id,
        role: data.role, full_name: data.full_name,
        email, is_active: true,
      });
      toast.success('Компания зарегистрирована!');
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Ошибка регистрации';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f0f1a',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: '#1a1a2e', borderRadius: 20, padding: '36px 40px',
        width: '100%', maxWidth: 440, boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
        border: '1px solid rgba(255,255,255,0.07)',
      }}>
        {/* Лого */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <div style={{ background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)', borderRadius: 16, padding: 14 }}>
              <TrendingUp size={30} color="#fff" />
            </div>
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>Sellex</h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>Регистрация новой компании</p>
        </div>

        <form onSubmit={handleSubmit}>
          <Field
            label="Название компании"
            icon={<Building2 size={16} />}
            value={companyName}
            onChange={setCompanyName}
            placeholder="ООО Ромашка"
          />
          <Field
            label="Ваше имя"
            icon={<User size={16} />}
            value={fullName}
            onChange={setFullName}
            placeholder="Иван Петров"
          />
          <Field
            label="Email"
            icon={<Mail size={16} />}
            value={email}
            onChange={setEmail}
            type="email"
            placeholder="ivan@company.ru"
          />
          <Field
            label="Пароль (минимум 6 символов)"
            icon={<Lock size={16} />}
            value={password}
            onChange={setPassword}
            type={showPwd ? 'text' : 'password'}
            placeholder="••••••••"
            suffix={
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '13px', marginTop: 6,
              background: loading ? 'rgba(45,212,191,0.5)' : 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)',
              color: '#fff', border: 'none', borderRadius: 10,
              fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.15s',
            }}
          >
            {loading ? 'Создаём аккаунт...' : 'Зарегистрироваться'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: '#64748b' }}>
          Уже есть аккаунт?{' '}
          <Link to="/login" style={{ color: '#2dd4bf', fontWeight: 600, textDecoration: 'none' }}>
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
}
