import React from 'react';
import { Bell } from 'lucide-react';
import { useAuthStore } from '../store/auth';

export default function Header() {
  const user = useAuthStore((s) => s.user);
  const initials = user?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'US';

  return (
    <header style={{
      height: 64, background: '#fff', borderBottom: '1px solid #e2e8f0',
      display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
      padding: '0 24px', gap: 16, position: 'sticky', top: 0, zIndex: 50,
    }}>
      <button style={{ background: 'none', border: 'none', color: '#64748b', padding: 8, borderRadius: 8 }}>
        <Bell size={20} />
      </button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%', background: '#6366f1',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 600, fontSize: 13,
        }}>
          {initials}
        </div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{user?.full_name}</div>
          <div style={{ fontSize: 12, color: '#64748b' }}>{user?.role}</div>
        </div>
      </div>
    </header>
  );
}
