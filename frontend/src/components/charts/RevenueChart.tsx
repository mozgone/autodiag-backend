import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { RevenueChartPoint } from '../../types';

interface Props { data: RevenueChartPoint[]; }

const fmt = (v: number) => v >= 1000000 ? `${(v/1000000).toFixed(1)}М` : v >= 1000 ? `${(v/1000).toFixed(0)}К` : String(v);

export default function RevenueChart({ data }: Props) {
  return (
    <div style={{ background: '#1a1a2e', borderRadius: 16, padding: '24px', border: '1px solid rgba(255,255,255,0.07)' }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: '#f1f5f9' }}>Выручка по неделям</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(v: number) => [`${v.toLocaleString('ru')} ₽`, 'Выручка']}
            contentStyle={{ borderRadius: 10, border: '1px solid rgba(255,255,255,0.1)', background: '#1a1a2e', color: '#f1f5f9', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}
            labelStyle={{ color: '#64748b' }}
          />
          <Area type="monotone" dataKey="revenue" stroke="#2dd4bf" strokeWidth={2.5} fill="url(#revGrad)" dot={{ fill: '#2dd4bf', r: 4, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
