import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { RevenueChartPoint } from '../../types';

interface Props { data: RevenueChartPoint[]; }

const fmt = (v: number) => v >= 1000000 ? `${(v/1000000).toFixed(1)}М` : v >= 1000 ? `${(v/1000).toFixed(0)}К` : String(v);

export default function RevenueChart({ data }: Props) {
  return (
    <div style={{ background: '#fff', borderRadius: 16, padding: '24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.07)' }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: '#1e293b' }}>Выручка по неделям</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <Tooltip formatter={(v: number) => [`${v.toLocaleString('ru')} ₽`, 'Выручка']} contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
          <Area type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={2.5} fill="url(#revGrad)" dot={{ fill: '#6366f1', r: 4 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
