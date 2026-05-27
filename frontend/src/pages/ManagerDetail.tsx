import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Phone, TrendingUp, Database, CheckCircle, AlertTriangle, Lightbulb, Target, MessageSquare, Clock, Star, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getManager } from '../api/client';
import { ManagerDetail as MgrDetail, Recommendation } from '../types';
import ManagerRadar from '../components/charts/ManagerRadar';

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

const recConfig: Record<string, { color: string; bg: string; icon: React.ElementType; label: string }> = {
  strength: { color: '#2dd4bf', bg: 'rgba(45,212,191,0.1)',   icon: CheckCircle,  label: 'Сильная сторона' },
  growth:   { color: '#fb923c', bg: 'rgba(251,146,60,0.1)',   icon: Lightbulb,    label: 'Зона роста'      },
  alert:    { color: '#f472b6', bg: 'rgba(244,114,182,0.1)',  icon: AlertTriangle, label: 'Внимание'        },
  forecast: { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', icon: Target,        label: 'Прогноз'         },
};

export default function ManagerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [period, setPeriod] = useState<Period>('week');

  const { data: manager, isLoading } = useQuery<MgrDetail>({
    queryKey: ['manager', id, period],
    queryFn: () => getManager(id!, period),
    enabled: !!id,
  });

  if (isLoading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>Загрузка...</div>
  );
  if (!manager) return (
    <div style={{ padding: 60, color: '#ef4444' }}>Менеджер не найден</div>
  );

  const stats = manager.stats;
  const plan = manager.monthly_plan;

  return (
    <div>
      {/* Назад */}
      <button onClick={() => navigate('/managers')} style={{
        display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none',
        color: '#2dd4bf', fontSize: 14, fontWeight: 500, marginBottom: 20, cursor: 'pointer',
      }}>
        <ArrowLeft size={16} /> Назад к менеджерам
      </button>

      {/* Шапка + period selector */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 24, fontWeight: 700,
          }}>
            {manager.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>{manager.full_name}</h1>
            <p style={{ color: '#64748b', fontSize: 14 }}>
              {manager.email} · План: {fmt(plan)}/мес.
            </p>
          </div>
        </div>

        {/* Period selector */}
        <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 4, border: '1px solid rgba(255,255,255,0.07)', alignSelf: 'center' }}>
          {PERIODS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              style={{
                padding: '7px 14px', borderRadius: 9, border: 'none', cursor: 'pointer',
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Ключевые метрики */}
        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#f1f5f9' }}>
            Ключевые метрики
          </h3>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Звонки',       value: stats.calls_count,                      icon: Phone,     color: '#a78bfa' },
                { label: 'Выручка',      value: fmt(stats.revenue),                     icon: TrendingUp, color: '#2dd4bf' },
                { label: 'Конверсия',    value: `${stats.conversion_rate?.toFixed(1)}%`, icon: Target,    color: '#fb923c' },
                { label: 'Заполн. CRM', value: `${stats.crm_fill_rate?.toFixed(0)}%`,   icon: Database,  color: '#60a5fa' },
              ].map(({ label, value, icon: Icon, color }) => (
                <div key={label} style={{ padding: 14, background: 'rgba(255,255,255,0.04)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Icon size={16} color={color} />
                    <span style={{ fontSize: 12, color: '#64748b' }}>{label}</span>
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Радар */}
        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: '#f1f5f9' }}>
            Профиль компетенций
          </h3>
          {stats && <ManagerRadar stats={stats} />}
        </div>
      </div>

      {/* Анализ коммуникаций */}
      {stats && (
        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <div style={{ background: 'rgba(45,212,191,0.12)', borderRadius: 10, padding: 8 }}>
              <MessageSquare size={18} color="#2dd4bf" />
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9' }}>Анализ коммуникаций</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
            {[
              {
                label: 'Качество звонков',
                value: stats.calls_quality_avg > 0 ? `${stats.calls_quality_avg.toFixed(1)}/10` : '—',
                icon: Star,
                color: stats.calls_quality_avg >= 7 ? '#2dd4bf' : stats.calls_quality_avg >= 5 ? '#fb923c' : stats.calls_quality_avg > 0 ? '#f472b6' : '#64748b',
                sub: stats.calls_quality_avg > 0 ? (stats.calls_quality_avg >= 7 ? 'Высокое' : stats.calls_quality_avg >= 5 ? 'Среднее' : 'Низкое') : 'Нет данных',
              },
              {
                label: 'Ср. длительность',
                value: stats.calls_duration_avg > 0
                  ? `${Math.floor(stats.calls_duration_avg / 60)}м ${Math.round(stats.calls_duration_avg % 60)}с`
                  : '—',
                icon: Clock,
                color: '#a78bfa',
                sub: 'на звонок',
              },
              {
                label: 'Активностей',
                value: stats.activities_count,
                icon: Activity,
                color: '#60a5fa',
                sub: 'за период',
              },
              {
                label: 'Заполн. CRM',
                value: `${stats.crm_fill_rate.toFixed(0)}%`,
                icon: Database,
                color: stats.crm_fill_rate >= 80 ? '#2dd4bf' : stats.crm_fill_rate >= 50 ? '#fb923c' : '#f472b6',
                sub: stats.crm_fill_rate >= 80 ? 'Хорошо' : stats.crm_fill_rate >= 50 ? 'Требует внимания' : 'Плохо',
              },
            ].map(({ label, value, icon: Icon, color, sub }) => (
              <div key={label} style={{ padding: 14, background: 'rgba(255,255,255,0.04)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Icon size={15} color={color} />
                  <span style={{ fontSize: 11, color: '#64748b' }}>{label}</span>
                </div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#f1f5f9', marginBottom: 2 }}>{value}</div>
                <div style={{ fontSize: 11, color }}>
                  {sub}
                </div>
              </div>
            ))}
          </div>

          {/* Визуальная шкала качества */}
          {stats.calls_quality_avg > 0 && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#64748b', marginBottom: 6 }}>
                <span>Качество коммуникаций (ИИ-оценка)</span>
                <span style={{ fontWeight: 600, color: stats.calls_quality_avg >= 7 ? '#2dd4bf' : stats.calls_quality_avg >= 5 ? '#fb923c' : '#f472b6' }}>
                  {(stats.calls_quality_avg / 10 * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 4 }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(stats.calls_quality_avg / 10 * 100, 100)}%`,
                  background: stats.calls_quality_avg >= 7 ? 'linear-gradient(90deg, #2dd4bf, #60a5fa)' : stats.calls_quality_avg >= 5 ? 'linear-gradient(90deg, #fb923c, #fbbf24)' : 'linear-gradient(90deg, #f472b6, #fb923c)',
                  borderRadius: 4,
                  transition: 'width 0.5s',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#475569', marginTop: 4 }}>
                <span>Плохо</span><span>Нормально</span><span>Отлично</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Динамика */}
      {manager.weekly_history.length > 0 && (
        <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)', marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#f1f5f9' }}>
            Динамика за период
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Выручка (₽)</p>
              <ResponsiveContainer width="100%" height={150}>
                <AreaChart data={manager.weekly_history}>
                  <defs>
                    <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#2dd4bf" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip
                    formatter={(v: number) => [fmt(v), 'Выручка']}
                    contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f1f5f9' }}
                  />
                  <Area type="monotone" dataKey="revenue" stroke="#2dd4bf" fill="url(#rg)" strokeWidth={2} dot={{ r: 3, fill: '#2dd4bf' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Звонки</p>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart data={manager.weekly_history}>
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f1f5f9' }}
                  />
                  <Bar dataKey="calls" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Рекомендации ИИ */}
      <div style={{ background: '#1a1a2e', borderRadius: 16, padding: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#f1f5f9' }}>
          Рекомендации ИИ ({manager.recommendations.length})
        </h3>
        {manager.recommendations.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: 14 }}>Рекомендации пока не сформированы.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {manager.recommendations.map((rec: Recommendation) => {
              const cfg = recConfig[rec.rec_type] || recConfig.forecast;
              const Icon = cfg.icon;
              return (
                <div key={rec.id} style={{ padding: 16, background: cfg.bg, borderRadius: 12, border: `1px solid ${cfg.color}40` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Icon size={16} color={cfg.color} />
                    <span style={{ fontSize: 12, fontWeight: 600, color: cfg.color }}>{cfg.label}</span>
                    {rec.priority === 3 && (
                      <span style={{ fontSize: 11, padding: '2px 8px', background: 'rgba(244,114,182,0.15)', color: '#f472b6', borderRadius: 99, fontWeight: 600 }}>
                        Важно
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>{rec.title}</div>
                  <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.5 }}>{rec.content}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
