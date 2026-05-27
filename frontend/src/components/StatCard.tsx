import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
  accentBg?: string;
}

export default function StatCard({ title, value, subtitle, icon: Icon, color = '#2dd4bf', trend, accentBg }: StatCardProps) {
  const trendColor = trend === 'up' ? '#2dd4bf' : trend === 'down' ? '#f472b6' : '#64748b';
  const bgColor = accentBg || `${color}12`;
  return (
    <div style={{
      background: '#1a1a2e', borderRadius: 16, padding: '20px 24px',
      border: '1px solid rgba(255,255,255,0.07)',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>{title}</span>
        <div style={{ background: bgColor, borderRadius: 10, padding: 8 }}>
          <Icon size={20} color={color} />
        </div>
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
        {subtitle && <div style={{ fontSize: 12, color: trendColor, marginTop: 4 }}>{subtitle}</div>}
      </div>
    </div>
  );
}
