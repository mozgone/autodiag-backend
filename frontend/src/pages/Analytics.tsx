import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRevenueChart, getRanking } from '../api/client';
import RevenueChart from '../components/charts/RevenueChart';
import { TrendingUp, TrendingDown } from 'lucide-react';

type Period = 'day' | 'week' | 'month' | 'year';
const PERIODS: { key: Period; label: string }[] = [
  { key: 'day',   label: 'День'   },
  { key: 'week',  label: 'Неделя' },
  { key: 'month', label: 'Месяц'  },
  { key: 'year',  label: 'Год'    },
];

const fmt = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}М ₽`
  : n >= 1_000   ? `${(n / 1_000).toFixed(0)}К ₽`
  : `${n} ₽`;

export default function Analytics() {
  const [period, setPeriod] = useState<Period>('week');

  const { data: chartData = [] } = useQuery({
    queryKey: ['revenue-chart', period],
    queryFn: () => getRevenueChart(period),
  });
  const { data: ranking = [], isLoading } = useQuery({
    queryKey: ['ranking', period],
    queryFn: () => getRanking(period),
  });

  return (
    <div>
      {/* Заголовок + period selector */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Аналитика</h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
            Детальные отчёты по отделу продаж
          </p>
        </div>
        <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 4, border: '1px solid rgba(255,255,255,0.07)' }}>
          {PERIODS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              style={{
                padding: '7px 16px', borderRadius: 9, border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 600, transition: 'all 0.15s',
                background: period === key ? 'linear-gradient(135deg, #2dd4bf, #a78bfa)' : 'transparent',
                color: period === key ? '#fff' : '#64748b',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <RevenueChart data={chartData} />
      </div>

      {/* Таблица рейтинга */}
      <div style={{ background: '#1a1a2e', borderRadius: 16, border: '1px solid rgba(255,255,255,0.07)', overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9' }}>Рейтинг менеджеров</h3>
        </div>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>Загрузка...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                {['#', 'Менеджер', 'Выручка', 'Конверсия', 'Звонки', 'План', 'Тренд'].map((h) => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranking.map((item: any) => (
                <tr key={item.manager_id} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: item.rank <= 3 ? '#fb923c' : '#64748b' }}>
                    {item.rank}
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#f1f5f9' }}>
                    {item.full_name}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#2dd4bf', fontWeight: 600 }}>
                    {fmt(item.revenue)}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#64748b' }}>
                    {item.conversion_rate?.toFixed(1)}%
                  </td>
                  <td style={{ padding: '14px 16px', color: '#64748b' }}>
                    {item.calls_count}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
                        <div style={{
                          height: '100%',
                          width: `${Math.min(item.plan_completion, 100)}%`,
                          background: item.plan_completion >= 100 ? '#2dd4bf' : item.plan_completion >= 70 ? '#fb923c' : '#f472b6',
                          borderRadius: 3,
                        }} />
                      </div>
                      <span style={{ fontSize: 12, color: '#64748b', width: 36 }}>
                        {item.plan_completion?.toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {item.trend === 'up'
                      ? <TrendingUp size={16} color="#2dd4bf" />
                      : <TrendingDown size={16} color="#f472b6" />
                    }
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
