import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Search, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getManagers } from '../api/client';
import { Manager } from '../types';

const fmt = (n: number) => n >= 1000000 ? `${(n/1000000).toFixed(1)}М` : n >= 1000 ? `${(n/1000).toFixed(0)}К` : String(n);

function PlanBar({ value }: { value: number }) {
  const pct = Math.min(value, 100);
  const color = pct >= 100 ? '#2dd4bf' : pct >= 70 ? '#fb923c' : '#f472b6';
  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4, color: '#64748b' }}>
        <span>Выполнение плана</span><span style={{ color, fontWeight: 600 }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.5s' }} />
      </div>
    </div>
  );
}

export default function Managers() {
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const { data: managers = [], isLoading, isError, refetch } = useQuery({ queryKey: ['managers', 'week'], queryFn: () => getManagers('week') });

  const filtered = managers.filter((m: Manager) =>
    m.full_name.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) return <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>Загрузка менеджеров...</div>;
  if (isError) return (
    <div style={{ textAlign: 'center', padding: 60 }}>
      <div style={{ color: '#f472b6', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Не удалось загрузить данные</div>
      <div style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>Сервер не отвечает. Подождите 30 секунд и попробуйте снова.</div>
      <button onClick={() => refetch()} style={{ padding: '10px 24px', background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>Повторить</button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Менеджеры</h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>{managers.length} сотрудников в системе</p>
        </div>
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск менеджера..."
            style={{
              paddingLeft: 36, paddingRight: 14, paddingTop: 10, paddingBottom: 10,
              border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: 10, fontSize: 14,
              outline: 'none', width: 240, background: '#1a1a2e', color: '#f1f5f9',
            }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
        {filtered.map((m: Manager) => {
          const stats = m.stats;
          const TrendIcon = stats?.trend === 'up' ? TrendingUp : stats?.trend === 'down' ? TrendingDown : Minus;
          const trendColor = stats?.trend === 'up' ? '#2dd4bf' : stats?.trend === 'down' ? '#f472b6' : '#64748b';
          return (
            <div
              key={m.id}
              onClick={() => navigate(`/managers/${m.id}`)}
              style={{
                background: '#1a1a2e', borderRadius: 16, padding: 24,
                border: '1px solid rgba(255,255,255,0.07)',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.border = '1px solid rgba(45,212,191,0.3)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.border = '1px solid rgba(255,255,255,0.07)'; e.currentTarget.style.transform = 'none'; }}
            >
              {/* Заголовок */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontWeight: 700, fontSize: 16,
                  }}>
                    {m.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 15 }}>{m.full_name}</div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{m.email || 'Менеджер'}</div>
                  </div>
                </div>
                <TrendIcon size={18} color={trendColor} />
              </div>

              {/* Метрики */}
              {stats && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 16 }}>
                    {[
                      { label: 'Звонки', value: stats.calls_count },
                      { label: 'Выручка', value: `${fmt(stats.revenue)} ₽` },
                      { label: 'Конверсия', value: `${stats.conversion_rate?.toFixed(0)}%` },
                    ].map(({ label, value }) => (
                      <div key={label} style={{ textAlign: 'center', padding: '10px 8px', background: 'rgba(255,255,255,0.04)', borderRadius: 10 }}>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
                        <div style={{ fontSize: 11, color: '#64748b' }}>{label}</div>
                      </div>
                    ))}
                  </div>
                  <PlanBar value={stats.plan_completion ?? 0} />
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
