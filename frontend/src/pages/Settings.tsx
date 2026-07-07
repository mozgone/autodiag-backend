import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCRMStatus, connectCRM, syncCRM, getMe, telegramUnlink, getAppInfo } from '../api/client';
import { useAuthStore } from '../store/auth';
import toast from 'react-hot-toast';
import {
  CheckCircle, Plug, Send, Unlink, RefreshCw, AlertCircle,
  Users, Clock, ExternalLink, Eye, EyeOff,
} from 'lucide-react';

interface CRMStatus {
  crm_type: string;
  is_connected: boolean;
  last_sync: string | null;
  sync_status: string | null;
  sync_error: string | null;
  managers_count: number;
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  const diff = Math.floor((Date.now() - d.getTime()) / 60000);
  if (diff < 1) return 'только что';
  if (diff < 60) return `${diff} мин. назад`;
  if (diff < 1440) return `${Math.floor(diff / 60)} ч. назад`;
  return d.toLocaleDateString('ru-RU');
}

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const { data: crmStatus, refetch: refetchCRM } = useQuery<CRMStatus>({
    queryKey: ['crm-status'],
    queryFn: getCRMStatus,
    refetchInterval: (query) => (query.state.data as CRMStatus | undefined)?.sync_status === 'syncing' ? 2000 : false,
  });
  const { data: userProfile } = useQuery({ queryKey: ['me'], queryFn: getMe });
  const { data: appInfo } = useQuery({ queryKey: ['app-info'], queryFn: getAppInfo });
  const queryClient = useQueryClient();

  // Форма amoCRM
  const [subdomain, setSubdomain] = useState('');
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [consent, setConsent] = useState(false);

  const isTgLinked = !!userProfile?.telegram_id;
  const botLink = appInfo?.bot_link || 'https://t.me/sellex_bot';
  const miniAppUrl = appInfo?.mini_app_url || null;

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['crm-status'] });
    queryClient.invalidateQueries({ queryKey: ['overview'] });
    queryClient.invalidateQueries({ queryKey: ['managers'] });
  };

  const connectMutation = useMutation({
    mutationFn: () => connectCRM({
      crm_type: 'amocrm',
      subdomain,
      access_token: token,
      consent,
    }),
    onSuccess: (data) => {
      toast.success(`amoCRM подключена! Загружено менеджеров: ${data.managers_synced}`);
      invalidateAll();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Ошибка подключения');
    },
  });

  const syncMutation = useMutation({
    mutationFn: syncCRM,
    onSuccess: (data) => {
      toast.success(`Синхронизация завершена. Менеджеров: ${data.managers_synced}`);
      invalidateAll();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Ошибка синхронизации');
    },
  });

  const unlinkTgMutation = useMutation({
    mutationFn: telegramUnlink,
    onSuccess: () => {
      toast.success('Telegram отвязан');
      queryClient.invalidateQueries({ queryKey: ['me'] });
    },
    onError: () => toast.error('Ошибка отвязки'),
  });

  const isSyncing = crmStatus?.sync_status === 'syncing'
    || connectMutation.isPending
    || syncMutation.isPending;

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '11px 14px',
    border: '1.5px solid rgba(255,255,255,0.1)',
    borderRadius: 10, fontSize: 14, outline: 'none',
    background: 'rgba(255,255,255,0.04)', color: '#f1f5f9',
    boxSizing: 'border-box',
  };
  const card: React.CSSProperties = {
    background: '#1a1a2e', borderRadius: 16, padding: 28,
    border: '1px solid rgba(255,255,255,0.07)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Настройки</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          Управление аккаунтом и подключение CRM
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Профиль */}
        <div style={card}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: '#f1f5f9' }}>
            Профиль
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Имя', value: user?.full_name || '' },
              { label: 'Email', value: user?.email || '' },
              { label: 'Роль', value: user?.role || '' },
            ].map(({ label, value }) => (
              <div key={label}>
                <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>
                  {label}
                </label>
                <input value={value} readOnly style={{ ...inputStyle, background: 'rgba(255,255,255,0.03)' }} />
              </div>
            ))}
          </div>
        </div>

        {/* CRM */}
        <div style={card}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9', marginBottom: 20 }}>
            Подключение CRM
          </h2>

          {/* Статус подключения */}
          {crmStatus?.is_connected ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Статус-бейдж */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 16px', background: 'rgba(45,212,191,0.08)',
                borderRadius: 12, border: '1px solid rgba(45,212,191,0.2)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <CheckCircle size={16} color="#2dd4bf" />
                  <span style={{ fontSize: 14, fontWeight: 600, color: '#2dd4bf' }}>
                    amoCRM подключена
                  </span>
                </div>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {crmStatus.crm_type}
                </span>
              </div>

              {/* Метрики синхронизации */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{
                  padding: '12px 14px', background: 'rgba(255,255,255,0.03)',
                  borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Users size={13} color="#64748b" />
                    <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>МЕНЕДЖЕРОВ</span>
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9' }}>
                    {crmStatus.managers_count}
                  </div>
                </div>
                <div style={{
                  padding: '12px 14px', background: 'rgba(255,255,255,0.03)',
                  borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Clock size={13} color="#64748b" />
                    <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>СИНХРОНИЗАЦИЯ</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9' }}>
                    {fmtDate(crmStatus.last_sync)}
                  </div>
                </div>
              </div>

              {/* Ошибка */}
              {crmStatus.sync_error && (
                <div style={{
                  display: 'flex', gap: 10, padding: '12px 14px',
                  background: 'rgba(244,114,182,0.08)', borderRadius: 10,
                  border: '1px solid rgba(244,114,182,0.2)',
                }}>
                  <AlertCircle size={16} color="#f472b6" style={{ flexShrink: 0, marginTop: 1 }} />
                  <span style={{ fontSize: 13, color: '#f472b6' }}>{crmStatus.sync_error}</span>
                </div>
              )}

              {/* Кнопка синхронизации */}
              <button
                onClick={() => syncMutation.mutate()}
                disabled={isSyncing}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '11px', background: isSyncing
                    ? 'rgba(45,212,191,0.2)'
                    : 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
                  color: '#fff', border: 'none', borderRadius: 10,
                  fontSize: 14, fontWeight: 600, cursor: isSyncing ? 'not-allowed' : 'pointer',
                }}
              >
                <RefreshCw size={15} style={{ animation: isSyncing ? 'spin 1s linear infinite' : 'none' }} />
                {isSyncing ? 'Синхронизация...' : 'Синхронизировать данные'}
              </button>
            </div>
          ) : (
            /* Форма подключения amoCRM */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Инструкция */}
              <div style={{
                padding: '12px 14px', background: 'rgba(255,255,255,0.03)',
                borderRadius: 10, border: '1px solid rgba(255,255,255,0.07)',
                fontSize: 13, color: '#94a3b8', lineHeight: 1.6,
              }}>
                <strong style={{ color: '#f1f5f9' }}>Как получить токен amoCRM:</strong>
                <ol style={{ margin: '8px 0 0 16px', padding: 0 }}>
                  <li>Откройте amoCRM → Настройки → Интеграции</li>
                  <li>Создайте новую интеграцию или откройте существующую</li>
                  <li>Скопируйте «Долгосрочный токен» (Long-lived token)</li>
                </ol>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>
                  Поддомен
                </label>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    value={subdomain}
                    onChange={(e) => setSubdomain(e.target.value)}
                    placeholder="yourcompany"
                    style={{ ...inputStyle, borderRadius: '10px 0 0 10px', flex: 1 }}
                  />
                  <span style={{
                    padding: '11px 12px', background: 'rgba(255,255,255,0.06)',
                    border: '1.5px solid rgba(255,255,255,0.1)', borderLeft: 'none',
                    borderRadius: '0 10px 10px 0', fontSize: 13, color: '#64748b', whiteSpace: 'nowrap',
                  }}>
                    .amocrm.ru
                  </span>
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>
                  Токен доступа (Long-lived token)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showToken ? 'text' : 'password'}
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Вставьте токен из настроек интеграции"
                    style={{ ...inputStyle, paddingRight: 44 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowToken(!showToken)}
                    style={{
                      position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0,
                    }}
                  >
                    {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 10, padding: 14,
                background: 'rgba(251,146,60,0.08)', borderRadius: 10,
                border: '1px solid rgba(251,146,60,0.2)',
              }}>
                <input
                  type="checkbox"
                  id="consent"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  style={{ marginTop: 2, cursor: 'pointer' }}
                />
                <label htmlFor="consent" style={{ fontSize: 12, color: '#fb923c', lineHeight: 1.5, cursor: 'pointer' }}>
                  Подтверждаю, что все сотрудники уведомлены об обработке персональных данных
                  и необходимые согласия получены.
                </label>
              </div>

              <button
                onClick={() => connectMutation.mutate()}
                disabled={connectMutation.isPending || !subdomain || !token || !consent}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '13px',
                  background: (connectMutation.isPending || !subdomain || !token || !consent)
                    ? 'rgba(45,212,191,0.2)'
                    : 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
                  color: '#fff', border: 'none', borderRadius: 10,
                  fontSize: 14, fontWeight: 600,
                  cursor: (connectMutation.isPending || !subdomain || !token || !consent)
                    ? 'not-allowed' : 'pointer',
                }}
              >
                <Plug size={16} />
                {connectMutation.isPending ? 'Подключение и синхронизация...' : 'Подключить amoCRM'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Telegram Mini App */}
      <div style={{ ...card, marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9' }}>Telegram Mini App</h2>
          {isTgLinked ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#2dd4bf', fontWeight: 600 }}>
              <CheckCircle size={14} /> Привязан
            </div>
          ) : (
            <div style={{ fontSize: 12, color: '#64748b' }}>Не привязан</div>
          )}
        </div>

        {isTgLinked ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{
              padding: '12px 14px', background: 'rgba(45,212,191,0.08)', borderRadius: 10,
              fontSize: 13, color: '#2dd4bf', border: '1px solid rgba(45,212,191,0.2)',
            }}>
              ✅ Ваш Telegram привязан. Дашборд открывается автоматически из бота.
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <a
                href={miniAppUrl || botLink}
                target="_blank" rel="noreferrer"
                style={{
                  flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '11px',
                  background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
                  color: '#fff', borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none',
                }}
              >
                <Send size={15} /> Открыть в Telegram
              </a>
              <button
                onClick={() => unlinkTgMutation.mutate()}
                disabled={unlinkTgMutation.isPending}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '11px 14px',
                  background: 'rgba(244,114,182,0.08)', color: '#f472b6',
                  border: '1px solid rgba(244,114,182,0.25)',
                  borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer',
                }}
              >
                <Unlink size={15} /> Отвязать
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{
              padding: '12px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: 10,
              fontSize: 13, color: '#94a3b8', lineHeight: 1.6, border: '1px solid rgba(255,255,255,0.07)',
            }}>
              <strong>Как привязать аккаунт:</strong>
              <ol style={{ margin: '8px 0 0 16px', padding: 0 }}>
                <li>Откройте бота Sellex в Telegram</li>
                <li>Нажмите кнопку «Открыть приложение»</li>
                <li>Введите ваш email и пароль от Sellex</li>
              </ol>
            </div>
            <a
              href={botLink}
              target="_blank" rel="noreferrer"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '12px',
                background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
                color: '#fff', borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none',
              }}
            >
              <Send size={16} /> Перейти к боту Sellex
            </a>
          </div>
        )}
      </div>

      <div style={{
        marginTop: 20, padding: '12px 16px',
        background: 'rgba(244,114,182,0.08)', borderRadius: 10,
        fontSize: 12, color: '#f472b6', border: '1px solid rgba(244,114,182,0.2)',
      }}>
        ⚠️ Все аналитические выводы системы носят рекомендательный характер.
        Компания-клиент является оператором персональных данных.
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
