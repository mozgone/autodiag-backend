import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRevenueChart, getRanking } from '../api/client';
import RevenueChart from '../components/charts/RevenueChart';
import { TrendingUp, TrendingDown } from 'lucide-react';

const fmt = (n: number) => n >= 1000000 ? `${(n/1000000).toFixed(1)}М ₽` : n >= 1000 ? `${(n/1000).toFixed(0)}К ₽` : `${n} ₽`;

export default function Analytics() {
  const { data: chartData = [] } = useQuery({ queryKey: ['revenue-chart'], queryFn: getRevenueChart });
  const { data: ranking = [], isLoading } = useQuery({ queryKey: ['ranking'], queryFn: getRanking });

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>Аналитика</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>Детальные отчёты по отделу продаж</p>
      </div>

      <div style={{ marginBottom: 24 }}>
        <RevenueChart data={chartData} />
      </div>

      {/* Таблица рейтинга */}
      <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #f1f5f9' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b' }}>Рейтинг менеджеров</h3>
        </div>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>Загрузка...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {['#', 'Менеджер', 'Выручка', 'Конверсия', 'Звонки', 'План', 'Тренд'].map((h) => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranking.map((item: any) => (
                <tr key={item.manager_id} style={{ borderTop: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: item.rank <= 3 ? '#d97706' : '#94a3b8' }}>{item.rank}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#1e293b' }}>{item.full_name}</td>
                  <td style={{ padding: '14px 16px', color: '#10b981', fontWeight: 600 }}>{fmt(item.revenue)}</td>
                  <td style={{ padding: '14px 16px', color: '#64748b' }}>{item.conversion_rate?.toFixed(1)}%</td>
                  <td style={{ padding: '14px 16px', color: '#64748b' }}>{item.calls_count}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 6, background: '#f1f5f9', borderRadius: 3 }}>
                        <div style={{ height: '100%', width: `${Math.min(item.plan_completion, 100)}%`, background: item.plan_completion >= 100 ? '#10b981' : item.plan_completion >= 70 ? '#f59e0b' : '#ef4444', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: 12, color: '#64748b', width: 36 }}>{item.plan_completion?.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {item.trend === 'up' ? <TrendingUp size={16} color="#10b981" /> : <TrendingDown size={16} color="#ef4444" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
