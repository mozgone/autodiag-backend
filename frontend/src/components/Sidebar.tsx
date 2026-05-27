import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, BarChart3, Settings, LogOut, TrendingUp } from 'lucide-react';
import { useAuthStore } from '../store/auth';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Дашборд' },
  { to: '/managers', icon: Users, label: 'Менеджеры' },
  { to: '/analytics', icon: BarChart3, label: 'Аналитика' },
  { to: '/settings', icon: Settings, label: 'Настройки' },
];

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    position: 'fixed', top: 0, left: 0, height: '100vh',
    width: 'var(--sidebar-width)', background: '#13132a',
    display: 'flex', flexDirection: 'column', zIndex: 100,
    borderRight: '1px solid rgba(255,255,255,0.06)',
  },
  logo: {
    padding: '24px 20px', display: 'flex', alignItems: 'center', gap: 10,
    borderBottom: '1px solid rgba(255,255,255,0.07)',
  },
  logoIcon: {
    width: 36, height: 36, borderRadius: 10,
    background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  logoText: { color: '#f1f5f9', fontSize: 20, fontWeight: 700, letterSpacing: '-0.5px' },
  nav: { flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 4 },
  bottom: { padding: '16px 12px', borderTop: '1px solid rgba(255,255,255,0.07)' },
  logoutBtn: {
    display: 'flex', alignItems: 'center', gap: 10, width: '100%',
    padding: '10px 12px', background: 'none', border: 'none',
    color: '#64748b', fontSize: 14, borderRadius: 8,
    transition: 'all 0.15s',
  },
};

export default function Sidebar() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <aside style={styles.sidebar}>
      <div style={styles.logo}>
        <div style={styles.logoIcon}>
          <TrendingUp size={18} color="#fff" />
        </div>
        <span style={styles.logoText}>Sellex</span>
      </div>
      <nav style={styles.nav}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to} to={to}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 12px', borderRadius: 8, fontSize: 14, fontWeight: 500,
              color: isActive ? '#f1f5f9' : '#64748b',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              transition: 'all 0.15s',
              textDecoration: 'none',
            })}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={styles.bottom}>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          <LogOut size={18} />
          Выйти
        </button>
      </div>
    </aside>
  );
}
