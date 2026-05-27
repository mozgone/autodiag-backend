import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Users, Zap, AlertCircle, Eye, EyeOff, ChevronRight, ArrowLeft, Phone, Target, DollarSign, Star } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTelegram } from '../hooks/useTelegram';
import { useAuthStore } from '../store/auth';
import { telegramAuth, telegramLoginAndLink, getOverview, getManagers, getManager } from '../api/client';
import { Manager, OverviewStats, ManagerDetail, Recommendation } from '../types';

const fmt = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}М ₽`
  : n >= 1_000   ? `${Math.round(n / 1_000)}К ₽`
  : `${n} ₽`;

// ─── Форма привязки ───────────────────────────────────────────────────────────

function LinkAccountForm({ initData, onLinked }: { initData: string; onLinked: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await telegramLoginAndLink({ init_data: initData, email, password });
      setAuth(data.access_token, { id: data.user_id, tenant_id: data.tenant_id, role: data.role, full_name: data.full_name, email, is_active: true });
      toast.success('Аккаунт привязан!');
      onLinked();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Ошибка привязки';
      toast.error(msg === 'not_linked' ? 'Аккаунт не найден' : msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a14', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 20px' }}>
      {/* Логотип */}
      <div style={{ marginBottom: 32, textAlign: 'center' }}>
        <div style={{ width: 72, height: 72, background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)', borderRadius: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
          <TrendingUp size={36} color="#fff" strokeWidth={2} />
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#fff', margin: '0 0 8px' }}>Sellex</h1>
        <p style={{ fontSize: 14, color: '#64748b', margin: 0, lineHeight: 1.5 }}>AI-аналитика отдела продаж</p>
      </div>

      {/* Карточка формы */}
      <div style={{ width: '100%', maxWidth: 380, background: '#12121e', borderRadius: 24, padding: '28px 24px', border: '1px solid rgba(255,255,255,0.06)' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', margin: '0 0 6px' }}>Войдите в аккаунт</h2>
        <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 24px', lineHeight: 1.5 }}>Привяжите Sellex к вашему Telegram</p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@company.ru" required
              style={{ width: '100%', padding: '14px 16px', background: 'rgba(255,255,255,0.04)', border: '1.5px solid rgba(255,255,255,0.08)', borderRadius: 14, fontSize: 15, color: '#f1f5f9', outline: 'none', boxSizing: 'border-box' }}
              onFocus={e => e.target.style.borderColor = '#2dd4bf'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
          </div>
          <div style={{ marginBottom: 24, position: 'relative' }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Пароль</label>
            <input type={showPwd ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required
              style={{ width: '100%', padding: '14px 48px 14px 16px', background: 'rgba(255,255,255,0.04)', border: '1.5px solid rgba(255,255,255,0.08)', borderRadius: 14, fontSize: 15, color: '#f1f5f9', outline: 'none', boxSizing: 'border-box' }}
              onFocus={e => e.target.style.borderColor = '#2dd4bf'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
            <button type="button" onClick={() => setShowPwd(!showPwd)}
              style={{ position: 'absolute', right: 14, bottom: 14, background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}>
              {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <button type="submit" disabled={loading}
            style={{ width: '100%', padding: '16px', background: loading ? 'rgba(45,212,191,0.4)' : 'linear-gradient(135deg, #2dd4bf, #a78bfa)', color: '#fff', border: 'none', borderRadius: 14, fontSize: 16, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', letterSpacing: '0.02em' }}>
            {loading ? 'Входим...' : 'Войти и привязать'}
          </button>
        </form>
      </div>

      <p style={{ marginTop: 20, fontSize: 12, color: '#475569', textAlign: 'center', lineHeight: 1.6 }}>
        После привязки Telegram будет автоматически<br />открывать дашборд без ввода пароля
      </p>
    </div>
  );
}

// ─── Дашборд ──────────────────────────────────────────────────────────────────

function TgDashboard() {
  const { data: ov, isLoading } = useQuery<OverviewStats>({ queryKey: ['overview'], queryFn: getOverview });
  const user = useAuthStore(s => s.user);

  if (isLoading) return <Loader />;
  if (!ov) return null;

  const plan = ov.plan_completion_avg;
  const planColor = plan >= 100 ? '#2dd4bf' : plan >= 70 ? '#fb923c' : '#f472b6';

  const tiles = [
    { label: 'Менеджеров', value: ov.total_managers, icon: Users, grad: 'linear-gradient(135deg, #1e3a5f, #1a2a4a)', accent: '#60a5fa' },
    { label: 'Выручка', value: fmt(ov.total_revenue_month), icon: DollarSign, grad: 'linear-gradient(135deg, #0d3d30, #0a2d22)', accent: '#2dd4bf' },
    { label: 'Конверсия', value: `${ov.avg_conversion_rate.toFixed(1)}%`, icon: Zap, grad: 'linear-gradient(135deg, #3d2a00, #2a1d00)', accent: '#fb923c' },
    { label: 'План', value: `${plan.toFixed(0)}%`, icon: Target, grad: plan >= 100 ? 'linear-gradient(135deg, #0d3d30, #0a2d22)' : plan >= 70 ? 'linear-gradient(135deg, #3d2a00, #2a1d00)' : 'linear-gradient(135deg, #3d0d2a, #2a0a1d)', accent: planColor },
  ];

  return (
    <div style={{ padding: '20px 16px 0' }}>
      {/* Приветствие */}
      <div style={{ marginBottom: 20 }}>
        <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 4px' }}>Добро пожаловать,</p>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', margin: 0 }}>{user?.full_name?.split(' ')[0] || 'Руководитель'}</h2>
      </div>

      {/* Плитки метрик */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        {tiles.map(({ label, value, icon: Icon, grad, accent }) => (
          <div key={label} style={{ background: grad, borderRadius: 20, padding: '18px 16px', border: `1px solid ${accent}20` }}>
            <div style={{ width: 36, height: 36, background: `${accent}20`, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <Icon size={18} color={accent} strokeWidth={2} />
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>{value}</div>
            <div style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Прогресс плана */}
      <div style={{ background: '#12121e', borderRadius: 20, padding: '18px 20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9' }}>Выполнение плана</span>
          <span style={{ fontSize: 16, fontWeight: 800, color: planColor }}>{plan.toFixed(0)}%</span>
        </div>
        <div style={{ height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 100 }}>
          <div style={{ height: '100%', width: `${Math.min(plan, 100)}%`, background: planColor, borderRadius: 100, transition: 'width 0.6s ease' }} />
        </div>
        {ov.top_performer && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 12 }}>
            <Star size={14} color="#fb923c" fill="#fb923c" />
            <span style={{ fontSize: 13, color: '#94a3b8' }}>Топ: <strong style={{ color: '#f1f5f9' }}>{ov.top_performer}</strong></span>
          </div>
        )}
      </div>

      {/* Алерт рисков */}
      {ov.at_risk_deals > 0 && (
        <div style={{ background: 'rgba(244,114,182,0.08)', borderRadius: 16, padding: '14px 16px', border: '1px solid rgba(244,114,182,0.2)', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 38, height: 38, background: 'rgba(244,114,182,0.15)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <AlertCircle size={20} color="#f472b6" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#f472b6' }}>{ov.at_risk_deals} сделки под риском</div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>Требуют вашего внимания</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Список менеджеров ────────────────────────────────────────────────────────

function TgManagers({ onSelect }: { onSelect: (id: string) => void }) {
  const { data: managers = [], isLoading } = useQuery<Manager[]>({ queryKey: ['managers'], queryFn: getManagers });
  if (isLoading) return <Loader />;

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <h2 style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', margin: '0 0 16px' }}>Менеджеры</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {managers.map((m) => {
          const plan = m.stats?.plan_completion ?? 0;
          const planColor = plan >= 100 ? '#2dd4bf' : plan >= 70 ? '#fb923c' : '#f472b6';
          const initials = m.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
          const revenue = m.stats?.revenue ?? 0;

          return (
            <button key={m.id} onClick={() => onSelect(m.id)}
              style={{ background: '#12121e', borderRadius: 20, padding: '16px', border: '1px solid rgba(255,255,255,0.06)', cursor: 'pointer', textAlign: 'left', width: '100%', display: 'flex', alignItems: 'center', gap: 14 }}>
              {/* Аватар */}
              <div style={{ width: 48, height: 48, borderRadius: 16, background: 'linear-gradient(135deg, #2dd4bf20, #a78bfa20)', border: '2px solid rgba(45,212,191,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span style={{ fontSize: 17, fontWeight: 800, color: '#2dd4bf' }}>{initials}</span>
              </div>

              {/* Инфо */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9', marginBottom: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.full_name}</div>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>{fmt(revenue)}</div>
                <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 100 }}>
                  <div style={{ height: '100%', width: `${Math.min(plan, 100)}%`, background: planColor, borderRadius: 100 }} />
                </div>
              </div>

              {/* % и стрелка */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                <span style={{ fontSize: 16, fontWeight: 800, color: planColor }}>{plan.toFixed(0)}%</span>
                <ChevronRight size={16} color="#475569" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Детали менеджера ─────────────────────────────────────────────────────────

function TgManagerDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const { tg } = useTelegram();
  const { data: m, isLoading } = useQuery<ManagerDetail>({ queryKey: ['manager', id], queryFn: () => getManager(id) });

  useEffect(() => {
    tg?.BackButton.show();
    tg?.BackButton.onClick(onBack);
    return () => { tg?.BackButton.hide(); tg?.BackButton.offClick(onBack); };
  }, [tg, onBack]);

  if (isLoading) return <Loader />;
  if (!m) return null;

  const plan = m.stats?.plan_completion ?? 0;
  const planColor = plan >= 100 ? '#2dd4bf' : plan >= 70 ? '#fb923c' : '#f472b6';
  const initials = m.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  const metrics = m.stats ? [
    { label: 'Звонки', value: m.stats.calls_count, icon: Phone, color: '#60a5fa' },
    { label: 'Выручка', value: fmt(m.stats.revenue), icon: DollarSign, color: '#2dd4bf' },
    { label: 'Конверсия', value: `${m.stats.conversion_rate.toFixed(1)}%`, icon: Zap, color: '#fb923c' },
    { label: 'CRM', value: `${m.stats.crm_fill_rate.toFixed(0)}%`, icon: Target, color: '#a78bfa' },
  ] : [];

  const recStyle: Record<string, { color: string; bg: string }> = {
    strength: { color: '#2dd4bf', bg: 'rgba(45,212,191,0.08)' },
    growth:   { color: '#fb923c', bg: 'rgba(251,146,60,0.08)' },
    alert:    { color: '#f472b6', bg: 'rgba(244,114,182,0.08)' },
    forecast: { color: '#a78bfa', bg: 'rgba(167,139,250,0.08)' },
  };

  return (
    <div style={{ padding: '16px 16px 0' }}>
      {/* Кнопка назад */}
      <button onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#2dd4bf', fontSize: 14, fontWeight: 600, cursor: 'pointer', padding: '0 0 16px', marginLeft: -4 }}>
        <ArrowLeft size={18} /> Назад
      </button>

      {/* Профиль */}
      <div style={{ background: '#12121e', borderRadius: 24, padding: '24px 20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 16, textAlign: 'center' }}>
        <div style={{ width: 72, height: 72, borderRadius: 22, background: 'linear-gradient(135deg, #2dd4bf30, #a78bfa30)', border: '2px solid rgba(45,212,191,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
          <span style={{ fontSize: 26, fontWeight: 800, color: '#2dd4bf' }}>{initials}</span>
        </div>
        <div style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>{m.full_name}</div>
        <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>План: {fmt(m.monthly_plan)}/мес.</div>
        <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 100, marginBottom: 8 }}>
          <div style={{ height: '100%', width: `${Math.min(plan, 100)}%`, background: planColor, borderRadius: 100 }} />
        </div>
        <div style={{ fontSize: 13, color: planColor, fontWeight: 700 }}>{plan.toFixed(0)}% плана</div>
      </div>

      {/* Метрики */}
      {metrics.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
          {metrics.map(({ label, value, icon: Icon, color }) => (
            <div key={label} style={{ background: '#12121e', borderRadius: 18, padding: '16px 14px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <Icon size={18} color={color} style={{ marginBottom: 10 }} />
              <div style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', marginBottom: 2 }}>{value}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Рекомендации */}
      {m.recommendations.length > 0 && (
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9', margin: '0 0 10px' }}>Рекомендации</h3>
          {m.recommendations.map((rec: Recommendation) => {
            const s = recStyle[rec.rec_type] || recStyle.forecast;
            return (
              <div key={rec.id} style={{ background: s.bg, borderRadius: 16, padding: '14px 16px', border: `1px solid ${s.color}25`, marginBottom: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: s.color, marginBottom: 6 }}>{rec.title}</div>
                <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>{rec.content}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Bottom Navigation ────────────────────────────────────────────────────────

type Tab = 'dashboard' | 'managers';

function BottomNav({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const items: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'dashboard', label: 'Дашборд', icon: TrendingUp },
    { key: 'managers',  label: 'Команда',  icon: Users },
  ];
  return (
    <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: '#0d0d1a', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', zIndex: 100, paddingBottom: 'max(12px, env(safe-area-inset-bottom))' }}>
      {items.map(({ key, label, icon: Icon }) => {
        const active = tab === key;
        return (
          <button key={key} onClick={() => setTab(key)} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5, background: 'none', border: 'none', cursor: 'pointer', padding: '12px 0 0', color: active ? '#2dd4bf' : '#475569', transition: 'color 0.15s' }}>
            <div style={{ width: 44, height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center', background: active ? 'rgba(45,212,191,0.12)' : 'transparent', borderRadius: 10, transition: 'background 0.15s' }}>
              <Icon size={20} strokeWidth={active ? 2.5 : 1.8} />
            </div>
            <span style={{ fontSize: 11, fontWeight: active ? 700 : 400, letterSpacing: '0.02em' }}>{label}</span>
          </button>
        );
      })}
    </div>
  );
}

// ─── Loader ───────────────────────────────────────────────────────────────────

function Loader() {
  return (
    <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 48, height: 48, background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
          <TrendingUp size={24} color="#fff" />
        </div>
        <div style={{ fontSize: 13, color: '#64748b' }}>Загрузка...</div>
      </div>
    </div>
  );
}

// ─── Основной компонент ───────────────────────────────────────────────────────

export default function TelegramApp() {
  const { tg, isInTelegram, initData } = useTelegram();
  const { setAuth, logout, isAuthenticated } = useAuthStore();
  const [tab, setTab] = useState<Tab>('dashboard');
  const [selectedMgr, setSelectedMgr] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      tg.setHeaderColor('#0d0d1a');
      tg.setBackgroundColor('#0a0a14');
    }
  }, [tg]);

  useEffect(() => {
    if (!isAuthenticated() && isInTelegram && initData) {
      telegramAuth({ init_data: initData })
        .then(data => setAuth(data.access_token, { id: data.user_id, tenant_id: data.tenant_id, role: data.role, full_name: data.full_name, email: '', is_active: true }))
        .catch(() => {})
        .finally(() => setAuthChecked(true));
    } else {
      setAuthChecked(true);
    }
  }, [isInTelegram, initData]); // eslint-disable-line

  if (!authChecked) return (
    <div style={{ minHeight: '100vh', background: '#0a0a14', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Loader />
    </div>
  );

  if (!isAuthenticated()) return <LinkAccountForm initData={initData} onLinked={() => {}} />;

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a14', fontFamily: "'Inter', -apple-system, sans-serif", maxWidth: 480, margin: '0 auto', color: '#f1f5f9' }}>
      <div style={{ paddingBottom: 88 }}>
        {selectedMgr ? (
          <TgManagerDetail id={selectedMgr} onBack={() => setSelectedMgr(null)} />
        ) : tab === 'dashboard' ? (
          <TgDashboard />
        ) : (
          <TgManagers onSelect={id => { setSelectedMgr(id); }} />
        )}
      </div>
      {!selectedMgr && <BottomNav tab={tab} setTab={t => { setTab(t); }} />}
    </div>
  );
}
