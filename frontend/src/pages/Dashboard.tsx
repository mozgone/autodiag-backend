import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, TrendingUp, DollarSign, AlertTriangle, BarChart3, Award } from 'lucide-react';
import { getOverview, getRevenueChart, getRanking } from '../api/client';
import StatCard from '../components/StatCard';
import RevenueChart from '../components/charts/RevenueChart';

const fmt = (n: number) => n >= 1000000 ? `${(n/1000000).toFixed(1)}М ₽` : n >= 1000 ? `${(n/1000).toFixed(0)}К ₽` : `${n} ₽`;

export default function Dashboard() {
  const { data: overview, isLoading: ovLoading } = useQuery({ queryKey: ['overview'], queryFn: getOverview });
  const { data: chartData = [] } = useQuery({ queryKey: ['revenue-chart'], queryFn: getRevenueChart });
  const { data: ranking = [] } = useQuery({ queryKey: ['ranking'], queryFn: getRanking });

  if (ovLoading) return <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>Загрузка дашборда...</div>;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Дашборд</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>Общая картина работы отдела продаж</p>
      </div>

      {/* KPI карточки */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard title="Менеджеров" value={overview?.total_managers ?? 0} icon={Users} color="#a78bfa" accentBg="rgba(167,139,250,0.12)" />
        <StatCard title="Выручка за месяц" value={fmt(overview?.total_revenue_month ?? 0)} icon={DollarSign} color="#2dd4bf" accentBg="rgba(45,212,191,0.12)"
          subtitle={`Средний план: ${overview?.plan_completion_avg?.toFixed(0)}%`} />
        <StatCard title="Конверсия" value={`${overview?.avg_conversion_rate?.toFixed(1)}%`} icon={TrendingUp} color="#fb923c" accentBg="rgba(251,146,60,0.12)" />
        <StatCard title="Сделок под риском" value={overview?.at_risk_deals ?? 0} icon={AlertTriangle} color="#f472b6" accentBg="rgba(244,114,182,0.12)" />
        <StatCard title="Топ-менеджер" value={overview?.top_performer ?? '—'} icon={Award} color="#60a5fa" accentBg="rgba(96,165,250,0.12)" />
      </div>

      {/* Графики */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 24 }}>
        <RevenueChart data={chartData} />

        {/* Топ менеджеры */}
        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#f1f5f9' }}>Рейтинг менеджеров</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {ranking.slice(0, 5).map((item: any) => (
              <div key={item.manager_id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: item.rank <= 3 ? 'rgba(251,146,60,0.18)' : 'rgba(255,255,255,0.06)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: item.rank <= 3 ? '#fb923c' : '#64748b',
                }}>
                  {item.rank}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9' }}>{item.full_name}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{item.plan_completion?.toFixed(0)}% плана</div>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#2dd4bf' }}>
                  {fmt(item.revenue)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{ padding: '12px 16px', background: 'rgba(251,146,60,0.1)', borderRadius: 10, fontSize: 12, color: '#fb923c', border: '1px solid rgba(251,146,60,0.25)' }}>
        ⚠️ Данные носят рекомендательный характер. Все выводы системы являются аналитическими оценками и не являются окончательными суждениями о работе сотрудников.
      </div>
    </div>
  );
}
