import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export default function StatCard({ title, value, subtitle, icon: Icon, color = '#6366f1', trend }: StatCardProps) {
  const trendColor = trend === 'up' ? '#10b981' : trend === 'down' ? '#ef4444' : '#64748b';
  return (
    <div style={{
      background: '#fff', borderRadius: 16, padding: '20px 24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.07)', border: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>{title}</span>
        <div style={{ background: `${color}15`, borderRadius: 10, padding: 8 }}>
          <Icon size={20} color={color} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 700, color: '#1e293b' }}>{value}</div>
        {subtitle && <div style={{ fontSize: 12, color: trendColor, marginTop: 4 }}>{subtitle}</div>}
      </div>
    </div>
  );
}
