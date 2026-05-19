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
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>Дашборд</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>Общая картина работы отдела продаж</p>
      </div>

      {/* KPI карточки */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard title="Менеджеров" value={overview?.total_managers ?? 0} icon={Users} color="#6366f1" />
        <StatCard title="Выручка за месяц" value={fmt(overview?.total_revenue_month ?? 0)} icon={DollarSign} color="#10b981"
          subtitle={`Средний план: ${overview?.plan_completion_avg?.toFixed(0)}%`} />
        <StatCard title="Конверсия" value={`${overview?.avg_conversion_rate?.toFixed(1)}%`} icon={TrendingUp} color="#f59e0b" />
        <StatCard title="Сделок под риском" value={overview?.at_risk_deals ?? 0} icon={AlertTriangle} color="#ef4444" />
        <StatCard title="Топ-менеджер" value={overview?.top_performer ?? '—'} icon={Award} color="#8b5cf6" />
      </div>

      {/* Графики */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 24 }}>
        <RevenueChart data={chartData} />

        {/* Топ менеджеры */}
        <div style={{ background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#1e293b' }}>Рейтинг менеджеров</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {ranking.slice(0, 5).map((item: any) => (
              <div key={item.manager_id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: item.rank <= 3 ? '#fef3c7' : '#f1f5f9',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: item.rank <= 3 ? '#d97706' : '#94a3b8',
                }}>
                  {item.rank}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{item.full_name}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{item.plan_completion?.toFixed(0)}% плана</div>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#10b981' }}>
                  {fmt(item.revenue)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{ padding: '12px 16px', background: '#fef3c7', borderRadius: 10, fontSize: 12, color: '#92400e', border: '1px solid #fde68a' }}>
        ⚠️ Данные носят рекомендательный характер. Все выводы системы являются аналитическими оценками и не являются окончательными суждениями о работе сотрудников.
      </div>
    </div>
  );
}
