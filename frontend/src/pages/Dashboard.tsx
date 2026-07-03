import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, TrendingUp, DollarSign, AlertTriangle, BarChart3, Award } from 'lucide-react';
import { getOverview, getRevenueChart, getRanking } from '../api/client';
import StatCard from '../components/StatCard';
import RevenueChart from '../components/charts/RevenueChart';

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

export default function Dashboard() {
  const [period, setPeriod] = useState<Period>('week');

  const { data: overview, isLoading: ovLoading, isError: ovError, refetch } = useQuery({
    queryKey: ['overview', period],
    queryFn: () => getOverview(period),
  });
  const { data: chartData = [] } = useQuery({
    queryKey: ['revenue-chart', period],
    queryFn: () => getRevenueChart(period),
  });
  const { data: ranking = [] } = useQuery({
    queryKey: ['ranking', period],
    queryFn: () => getRanking(period),
  });

  if (ovLoading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
      Загрузка дашборда...
      <div style={{ fontSize: 12, marginTop: 8, color: '#475569' }}>Соединение с сервером...</div>
    </div>
  );

  if (ovError) return (
    <div style={{ textAlign: 'center', padding: 60 }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
      <div style={{ color: '#f472b6', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Не удалось загрузить данные</div>
      <div style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>
        Сервер не отвечает. Возможно, он запускается — подождите 30 секунд и попробуйте снова.
      </div>
      <button
        onClick={() => refetch()}
        style={{
          padding: '10px 24px', background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
          color: '#fff', border: 'none', borderRadius: 10, fontSize: 14,
          fontWeight: 600, cursor: 'pointer',
        }}
      >
        Повторить
      </button>
    </div>
  );

  const periodLabel: Record<Period, string> = {
    day: 'за сегодня', week: 'за неделю', month: 'за месяц', year: 'за год',
  };

  return (
    <div>
      {/* Заголовок + period selector */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Дашборд</h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
            Общая картина работы отдела продаж
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

      {/* KPI карточки */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard
          title="Менеджеров"
          value={overview?.total_managers ?? 0}
          icon={Users} color="#a78bfa" accentBg="rgba(167,139,250,0.12)"
        />
        <StatCard
          title={`Выручка ${periodLabel[period]}`}
          value={fmt(overview?.total_revenue_month ?? 0)}
          icon={DollarSign} color="#2dd4bf" accentBg="rgba(45,212,191,0.12)"
          subtitle={`Средний план: ${overview?.plan_completion_avg?.toFixed(0)}%`}
        />
        <StatCard
          title="Конверсия"
          value={`${overview?.avg_conversion_rate?.toFixed(1)}%`}
          icon={TrendingUp} color="#fb923c" accentBg="rgba(251,146,60,0.12)"
        />
        <StatCard
          title="Под риском"
          value={overview?.at_risk_deals ?? 0}
          icon={AlertTriangle} color="#f472b6" accentBg="rgba(244,114,182,0.12)"
        />
        <StatCard
          title="Топ-менеджер"
          value={overview?.top_performer ?? '—'}
          icon={Award} color="#60a5fa" accentBg="rgba(96,165,250,0.12)"
        />
      </div>

      {/* Графики */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 24 }}>
        <RevenueChart data={chartData} />

        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#f1f5f9' }}>
            Рейтинг менеджеров
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {ranking.slice(0, 5).map((item: any) => (
              <div key={item.manager_id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: item.rank <= 3 ? 'rgba(251,146,60,0.18)' : 'rgba(255,255,255,0.06)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                  color: item.rank <= 3 ? '#fb923c' : '#64748b',
                }}>
                  {item.rank}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9' }}>
                    {item.full_name}
                  </div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>
                    {item.plan_completion?.toFixed(0)}% плана
                  </div>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#2dd4bf' }}>
                  {fmt(item.revenue)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ padding: '12px 16px', background: 'rgba(251,146,60,0.1)', borderRadius: 10, fontSize: 12, color: '#fb923c', border: '1px solid rgba(251,146,60,0.25)' }}>
        ⚠️ Данные носят рекомендательный характер. Все выводы системы являются аналитическими оценками и не являются окончательными суждениями о работе сотрудников.
      </div>
    </div>
  );
}
