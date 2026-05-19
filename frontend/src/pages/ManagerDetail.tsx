import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Phone, TrendingUp, Database, CheckCircle, AlertTriangle, Lightbulb, Target } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getManager } from '../api/client';
import { ManagerDetail as MgrDetail, Recommendation } from '../types';
import ManagerRadar from '../components/charts/ManagerRadar';

const fmt = (n: number) => n >= 1000000 ? `${(n/1000000).toFixed(1)}М ₽` : n >= 1000 ? `${(n/1000).toFixed(0)}К ₽` : `${n} ₽`;

const recConfig: Record<string, { color: string; bg: string; icon: React.ElementType; label: string }> = {
  strength: { color: '#10b981', bg: '#ecfdf5', icon: CheckCircle, label: 'Сильная сторона' },
  growth: { color: '#f59e0b', bg: '#fffbeb', icon: Lightbulb, label: 'Зона роста' },
  alert: { color: '#ef4444', bg: '#fef2f2', icon: AlertTriangle, label: 'Внимание' },
  forecast: { color: '#6366f1', bg: '#eef2ff', icon: Target, label: 'Прогноз' },
};

export default function ManagerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: manager, isLoading } = useQuery<MgrDetail>({
    queryKey: ['manager', id],
    queryFn: () => getManager(id!),
    enabled: !!id,
  });

  if (isLoading) return <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>Загрузка...</div>;
  if (!manager) return <div style={{ padding: 60, color: '#ef4444' }}>Менеджер не найден</div>;

  const stats = manager.stats;
  const plan = manager.monthly_plan;

  return (
    <div>
      {/* Назад */}
      <button onClick={() => navigate('/managers')} style={{
        display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none',
        color: '#6366f1', fontSize: 14, fontWeight: 500, marginBottom: 20,
      }}>
        <ArrowLeft size={16} /> Назад к менеджерам
      </button>

      {/* Шапка */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 28 }}>
        <div style={{
          width: 64, height: 64, borderRadius: '50%', background: '#6366f1',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 24, fontWeight: 700,
        }}>
          {manager.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
        </div>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>{manager.full_name}</h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>{manager.email} · План: {fmt(plan)}/мес.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Ключевые метрики */}
        <div style={{ background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#1e293b' }}>Ключевые метрики</h3>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Звонки', value: stats.calls_count, icon: Phone, color: '#6366f1' },
                { label: 'Выручка', value: fmt(stats.revenue), icon: TrendingUp, color: '#10b981' },
                { label: 'Конверсия', value: `${stats.conversion_rate?.toFixed(1)}%`, icon: Target, color: '#f59e0b' },
                { label: 'Заполн. CRM', value: `${stats.crm_fill_rate?.toFixed(0)}%`, icon: Database, color: '#8b5cf6' },
              ].map(({ label, value, icon: Icon, color }) => (
                <div key={label} style={{ padding: 14, background: '#f8fafc', borderRadius: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Icon size={16} color={color} />
                    <span style={{ fontSize: 12, color: '#64748b' }}>{label}</span>
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>{value}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Радар */}
        <div style={{ background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: '#1e293b' }}>Профиль компетенций</h3>
          {stats && <ManagerRadar stats={stats} />}
        </div>
      </div>

      {/* Динамика по неделям */}
      {manager.weekly_history.length > 0 && (
        <div style={{ background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0', marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#1e293b' }}>Динамика по неделям</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Выручка (₽)</p>
              <ResponsiveContainer width="100%" height={150}>
                <AreaChart data={manager.weekly_history}>
                  <defs><linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366f1" stopOpacity={0.15}/><stop offset="95%" stopColor="#6366f1" stopOpacity={0}/></linearGradient></defs>
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip formatter={(v: number) => [fmt(v), 'Выручка']} />
                  <Area type="monotone" dataKey="revenue" stroke="#6366f1" fill="url(#rg)" strokeWidth={2} dot={{ r: 3 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Звонки</p>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart data={manager.weekly_history}>
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip />
                  <Bar dataKey="calls" fill="#818cf8" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Рекомендации */}
      <div style={{ background: '#fff', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0' }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#1e293b' }}>
          Рекомендации ИИ ({manager.recommendations.length})
        </h3>
        {manager.recommendations.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Рекомендации пока не сформированы.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {manager.recommendations.map((rec: Recommendation) => {
              const cfg = recConfig[rec.rec_type] || recConfig.forecast;
              const Icon = cfg.icon;
              return (
                <div key={rec.id} style={{ padding: 16, background: cfg.bg, borderRadius: 12, border: `1px solid ${cfg.color}25` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Icon size={16} color={cfg.color} />
                    <span style={{ fontSize: 12, fontWeight: 600, color: cfg.color }}>{cfg.label}</span>
                    {rec.priority === 3 && <span style={{ fontSize: 11, padding: '2px 8px', background: '#ef444415', color: '#ef4444', borderRadius: 99, fontWeight: 600 }}>Важно</span>}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b', marginBottom: 4 }}>{rec.title}</div>
                  <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>{rec.content}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
