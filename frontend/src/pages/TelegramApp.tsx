/**
 * Sellex Telegram Mini App
 * Запускается внутри Telegram — единый стиль с веб-версией (#6366f1, Inter).
 * Маршрут: /tg
 *
 * Сценарии:
 * 1. Первый запуск → показываем форму привязки web-аккаунта
 * 2. Уже привязан → авто-вход, показываем дашборд
 */
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, BarChart3, Users, Lightbulb, CheckCircle, AlertTriangle, Eye, EyeOff, LogOut } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTelegram } from '../hooks/useTelegram';
import { useAuthStore } from '../store/auth';
import { telegramAuth, telegramLoginAndLink, getOverview, getManagers, getManager } from '../api/client';
import { Manager, OverviewStats, ManagerDetail, Recommendation } from '../types';

// ─── Общие стили ──────────────────────────────────────────────────────────────

const C = {
  primary:  '#6366f1',
  dark:     '#1e293b',
  muted:    '#64748b',
  bg:       '#f8fafc',
  white:    '#fff',
  border:   '#e2e8f0',
  success:  '#10b981',
  warning:  '#f59e0b',
  danger:   '#ef4444',
};

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: C.white, borderRadius: 16, padding: 16,
  border: `1px solid ${C.border}`, boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  ...extra,
});

const fmt = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}М ₽`
  : n >= 1_000   ? `${(n / 1_000).toFixed(0)}К ₽`
  : `${n} ₽`;

// ─── Форма привязки аккаунта ──────────────────────────────────────────────────

function LinkAccountForm({ initData, onLinked }: { initData: string; onLinked: () => void }) {
  const [email, setEmail]     = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await telegramLoginAndLink({ init_data: initData, email, password });
      setAuth(data.access_token, {
        id: data.user_id, tenant_id: data.tenant_id,
        role: data.role, full_name: data.full_name,
        email, is_active: true,
      });
      toast.success('Аккаунт привязан!');
      onLinked();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Ошибка привязки';
      toast.error(msg === 'not_linked' ? 'Аккаунт не найден' : msg);
    } finally {
      setLoading(false);
    }
  };

  const inp: React.CSSProperties = {
    width: '100%', padding: '12px 14px', border: `1.5px solid ${C.border}`,
    borderRadius: 10, fontSize: 14, outline: 'none', boxSizing: 'border-box',
  };

  return (
    <div style={{ minHeight: '100vh', background: `linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ background: C.white, borderRadius: 20, padding: 28, width: '100%', maxWidth: 380, boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ background: C.primary, borderRadius: 14, padding: 12, display: 'inline-flex', marginBottom: 12 }}>
            <TrendingUp size={28} color="#fff" />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: C.dark, marginBottom: 6 }}>Sellex</h1>
          <p style={{ color: C.muted, fontSize: 13, lineHeight: 1.5 }}>
            Войдите в ваш аккаунт Sellex, чтобы привязать его к Telegram
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 12, fontWeight: 500, color: C.muted, display: 'block', marginBottom: 6 }}>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.ru" required style={inp}
              onFocus={(e) => (e.target.style.borderColor = C.primary)}
              onBlur={(e) => (e.target.style.borderColor = C.border)}
            />
          </div>
          <div style={{ marginBottom: 20, position: 'relative' }}>
            <label style={{ fontSize: 12, fontWeight: 500, color: C.muted, display: 'block', marginBottom: 6 }}>Пароль</label>
            <input type={showPwd ? 'text' : 'password'} value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••" required style={{ ...inp, paddingRight: 40 }}
              onFocus={(e) => (e.target.style.borderColor = C.primary)}
              onBlur={(e) => (e.target.style.borderColor = C.border)}
            />
            <button type="button" onClick={() => setShowPwd(!showPwd)}
              style={{ position: 'absolute', right: 12, top: 30, background: 'none', border: 'none', color: C.muted, cursor: 'pointer' }}>
              {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          <button type="submit" disabled={loading}
            style={{ width: '100%', padding: '13px', background: loading ? '#a5b4fc' : C.primary, color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Вход...' : 'Войти и привязать'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: C.muted, lineHeight: 1.5 }}>
          После привязки Telegram будет автоматически открывать дашборд без ввода пароля.
        </p>
      </div>
    </div>
  );
}

// ─── KPI-карточка ─────────────────────────────────────────────────────────────

function KpiCard({ label, value, color = C.primary }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={card({ padding: '14px 16px' })}>
      <div style={{ fontSize: 11, color: C.muted, marginBottom: 4, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

// ─── Вкладка Дашборд ──────────────────────────────────────────────────────────

function TgDashboard() {
  const { data: ov, isLoading } = useQuery<OverviewStats>({ queryKey: ['overview'], queryFn: getOverview });
  if (isLoading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Загрузка...</div>;
  if (!ov) return null;
  const plan = ov.plan_completion_avg;
  const planColor = plan >= 100 ? C.success : plan >= 70 ? C.warning : C.danger;
  return (
    <div style={{ padding: '16px 16px 0' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <KpiCard label="Менеджеров" value={ov.total_managers} />
        <KpiCard label="Выручка" value={fmt(ov.total_revenue_month)} color={C.success} />
        <KpiCard label="Конверсия" value={`${ov.avg_conversion_rate.toFixed(1)}%`} color={C.warning} />
        <KpiCard label="Выполнение плана" value={`${plan.toFixed(0)}%`} color={planColor} />
      </div>

      {/* Прогресс-бар плана */}
      <div style={card({ marginBottom: 12 })}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 13, fontWeight: 600, color: C.dark }}>
          <span>Прогресс плана</span>
          <span style={{ color: planColor }}>{plan.toFixed(0)}%</span>
        </div>
        <div style={{ height: 8, background: '#f1f5f9', borderRadius: 4 }}>
          <div style={{ height: '100%', width: `${Math.min(plan, 100)}%`, background: planColor, borderRadius: 4, transition: 'width 0.5s' }} />
        </div>
        <div style={{ fontSize: 12, color: C.muted, marginTop: 8 }}>
          🏆 Топ-менеджер: <strong>{ov.top_performer || '—'}</strong>
        </div>
      </div>

      {/* Алерт рисков */}
      {ov.at_risk_deals > 0 && (
        <div style={{ padding: '12px 14px', background: '#fef2f2', borderRadius: 12, border: `1px solid #fecaca`, display: 'flex', alignItems: 'center', gap: 10 }}>
          <AlertTriangle size={18} color={C.danger} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#991b1b' }}>Сделки под риском: {ov.at_risk_deals}</div>
            <div style={{ fontSize: 11, color: '#b91c1c' }}>Требуют внимания</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Вкладка Менеджеры ────────────────────────────────────────────────────────

function TgManagers({ onSelectManager }: { onSelectManager: (id: string) => void }) {
  const { data: managers = [], isLoading } = useQuery<Manager[]>({ queryKey: ['managers'], queryFn: getManagers });
  if (isLoading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Загрузка...</div>;
  return (
    <div style={{ padding: '16px 16px 0' }}>
      {managers.map((m) => {
        const stats = m.stats;
        const plan = stats?.plan_completion ?? 0;
        const planColor = plan >= 100 ? C.success : plan >= 70 ? C.warning : C.danger;
        const initials = m.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2);
        return (
          <div key={m.id} onClick={() => onSelectManager(m.id)}
            style={{ ...card({ marginBottom: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }) }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: C.primary, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 16, flexShrink: 0 }}>
              {initials}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, color: C.dark, fontSize: 14, marginBottom: 4 }}>{m.full_name}</div>
              <div style={{ height: 5, background: '#f1f5f9', borderRadius: 3 }}>
                <div style={{ height: '100%', width: `${Math.min(plan, 100)}%`, background: planColor, borderRadius: 3 }} />
              </div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: planColor, flexShrink: 0 }}>{plan.toFixed(0)}%</div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Детальная карточка менеджера ─────────────────────────────────────────────

function TgManagerDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const { tg } = useTelegram();
  const { data: m, isLoading } = useQuery<ManagerDetail>({ queryKey: ['manager', id], queryFn: () => getManager(id) });

  useEffect(() => {
    tg?.BackButton.show();
    tg?.BackButton.onClick(onBack);
    return () => { tg?.BackButton.hide(); tg?.BackButton.offClick(onBack); };
  }, [tg, onBack]);

  if (isLoading) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Загрузка...</div>;
  if (!m) return null;

  const recConfig: Record<string, { color: string; bg: string; icon: React.ElementType }> = {
    strength: { color: C.success, bg: '#ecfdf5', icon: CheckCircle },
    growth:   { color: C.warning, bg: '#fffbeb', icon: Lightbulb },
    alert:    { color: C.danger,  bg: '#fef2f2', icon: AlertTriangle },
    forecast: { color: C.primary, bg: '#eef2ff', icon: TrendingUp },
  };

  return (
    <div style={{ padding: '16px 16px 0' }}>
      {/* Кнопка назад (для браузера, в TG используется BackButton) */}
      <button onClick={onBack} style={{ background: 'none', border: 'none', color: C.primary, fontSize: 14, fontWeight: 500, cursor: 'pointer', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
        ← Назад
      </button>

      {/* Шапка */}
      <div style={card({ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 })}>
        <div style={{ width: 52, height: 52, borderRadius: '50%', background: C.primary, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700 }}>
          {m.full_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
        </div>
        <div>
          <div style={{ fontWeight: 700, color: C.dark, fontSize: 16 }}>{m.full_name}</div>
          <div style={{ fontSize: 12, color: C.muted }}>План: {fmt(m.monthly_plan)}/мес.</div>
        </div>
      </div>

      {/* Метрики */}
      {m.stats && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
          <KpiCard label="Звонки" value={m.stats.calls_count} />
          <KpiCard label="Выручка" value={fmt(m.stats.revenue)} color={C.success} />
          <KpiCard label="Конверсия" value={`${m.stats.conversion_rate.toFixed(1)}%`} color={C.warning} />
          <KpiCard label="CRM" value={`${m.stats.crm_fill_rate.toFixed(0)}%`} color={C.primary} />
        </div>
      )}

      {/* Рекомендации */}
      {m.recommendations.length > 0 && (
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.dark, marginBottom: 8 }}>
            Рекомендации ({m.recommendations.length})
          </div>
          {m.recommendations.map((rec: Recommendation) => {
            const cfg = recConfig[rec.rec_type] || recConfig.forecast;
            const Icon = cfg.icon;
            return (
              <div key={rec.id} style={{ ...card({ marginBottom: 8, background: cfg.bg, border: `1px solid ${cfg.color}25` }) }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <Icon size={14} color={cfg.color} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: cfg.color }}>{rec.title}</span>
                </div>
                <div style={{ fontSize: 13, color: C.muted, lineHeight: 1.5 }}>{rec.content}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Нижняя навигация ─────────────────────────────────────────────────────────

type Tab = 'dashboard' | 'managers';

function BottomNav({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const items: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'dashboard', label: 'Дашборд',    icon: BarChart3 },
    { key: 'managers',  label: 'Менеджеры',  icon: Users },
  ];
  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: '#fff', borderTop: `1px solid ${C.border}`,
      display: 'flex', padding: '8px 0 max(8px, env(safe-area-inset-bottom))',
      zIndex: 100,
    }}>
      {items.map(({ key, label, icon: Icon }) => (
        <button key={key} onClick={() => setTab(key)}
          style={{
            flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
            background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0',
            color: tab === key ? C.primary : C.muted, transition: 'color 0.15s',
          }}>
          <Icon size={22} />
          <span style={{ fontSize: 11, fontWeight: tab === key ? 600 : 400 }}>{label}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Шапка приложения ─────────────────────────────────────────────────────────

function TgHeader({ onLogout }: { onLogout: () => void }) {
  return (
    <div style={{
      background: C.primary, padding: '14px 16px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 50,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingUp size={20} color="#fff" />
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 17 }}>Sellex</span>
      </div>
      <button onClick={onLogout}
        style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', color: '#fff' }}>
        <LogOut size={16} />
      </button>
    </div>
  );
}

// ─── Основной компонент ───────────────────────────────────────────────────────

export default function TelegramApp() {
  const { tg, isInTelegram, initData } = useTelegram();
  const { token, setAuth, logout, isAuthenticated } = useAuthStore();
  const [tab, setTab]             = useState<Tab>('dashboard');
  const [selectedMgr, setSelectedMgr] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Инициализация Telegram Web App
  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      // Устанавливаем наши цвета, а не Telegram-овские
      tg.setHeaderColor('#6366f1');
      tg.setBackgroundColor('#f8fafc');
    }
  }, [tg]);

  // Попытка авто-входа через Telegram initData
  useEffect(() => {
    if (!isAuthenticated() && isInTelegram && initData) {
      telegramAuth({ init_data: initData })
        .then((data) => {
          setAuth(data.access_token, {
            id: data.user_id, tenant_id: data.tenant_id,
            role: data.role, full_name: data.full_name,
            email: '', is_active: true,
          });
        })
        .catch(() => { /* not_linked — покажем форму привязки */ })
        .finally(() => setAuthChecked(true));
    } else {
      setAuthChecked(true);
    }
  }, [isInTelegram, initData]); // eslint-disable-line

  const handleLogout = () => { logout(); };
  const handleLinked = () => { /* после привязки стейт уже обновился через setAuth */ };

  if (!authChecked) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: C.bg }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ background: C.primary, borderRadius: 16, padding: 14, display: 'inline-flex', marginBottom: 12 }}>
            <TrendingUp size={28} color="#fff" />
          </div>
          <div style={{ color: C.muted, fontSize: 14 }}>Загрузка...</div>
        </div>
      </div>
    );
  }

  // Не авторизован → форма привязки аккаунта
  if (!isAuthenticated()) {
    return <LinkAccountForm initData={initData} onLinked={handleLinked} />;
  }

  // Авторизован → мини-приложение
  return (
    <div style={{ minHeight: '100vh', background: C.bg, fontFamily: "'Inter', sans-serif", maxWidth: 480, margin: '0 auto' }}>
      {/* Шапка только если не в Telegram (Telegram своя шапка через setHeaderColor) */}
      {!isInTelegram && <TgHeader onLogout={handleLogout} />}

      {/* Контент */}
      <div style={{ paddingBottom: 80 }}>
        {selectedMgr ? (
          <TgManagerDetail id={selectedMgr} onBack={() => setSelectedMgr(null)} />
        ) : tab === 'dashboard' ? (
          <TgDashboard />
        ) : (
          <TgManagers onSelectManager={(id) => setSelectedMgr(id)} />
        )}
      </div>

      {/* Нижняя навигация (только когда не в детали менеджера) */}
      {!selectedMgr && <BottomNav tab={tab} setTab={(t) => { setTab(t); }} />}
    </div>
  );
}
