import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCRMStatus, connectCRM, getMe, telegramUnlink, getAppInfo } from '../api/client';
import { useAuthStore } from '../store/auth';
import toast from 'react-hot-toast';
import { CheckCircle, Plug, Send, LinkIcon, Unlink } from 'lucide-react';

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const { data: crmStatus } = useQuery({ queryKey: ['crm-status'], queryFn: getCRMStatus });
  const { data: userProfile } = useQuery({ queryKey: ['me'], queryFn: getMe });
  const { data: appInfo }     = useQuery({ queryKey: ['app-info'], queryFn: getAppInfo });
  const [crmType, setCrmType] = useState('mock');
  const [subdomain, setSubdomain] = useState('');
  const [token, setToken] = useState('');
  const [consent, setConsent] = useState(false);
  const queryClient = useQueryClient();

  const unlinkTgMutation = useMutation({
    mutationFn: telegramUnlink,
    onSuccess: () => {
      toast.success('Telegram отвязан');
      queryClient.invalidateQueries({ queryKey: ['me'] });
    },
    onError: () => toast.error('Ошибка отвязки'),
  });

  const isTgLinked  = !!userProfile?.telegram_id;
  const botLink     = appInfo?.bot_link     || 'https://t.me/sellex_bot';
  const miniAppUrl  = appInfo?.mini_app_url || null;

  const connectMutation = useMutation({
    mutationFn: () => connectCRM({ crm_type: crmType, subdomain, access_token: token }),
    onSuccess: () => {
      toast.success('CRM успешно подключена!');
      queryClient.invalidateQueries({ queryKey: ['crm-status'] });
    },
    onError: () => toast.error('Ошибка подключения CRM'),
  });

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '11px 14px', border: '1.5px solid rgba(255,255,255,0.1)',
    borderRadius: 10, fontSize: 14, outline: 'none',
    background: 'rgba(255,255,255,0.04)', color: '#f1f5f9',
  };
  const card: React.CSSProperties = {
    background: '#1a1a2e', borderRadius: 16, padding: 28, border: '1px solid rgba(255,255,255,0.07)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>Настройки</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>Управление аккаунтом и подключение CRM</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Профиль */}
        <div style={card}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: '#f1f5f9' }}>Профиль</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Имя', value: user?.full_name || '' },
              { label: 'Email', value: user?.email || '' },
              { label: 'Роль', value: user?.role || '' },
            ].map(({ label, value }) => (
              <div key={label}>
                <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>{label}</label>
                <input value={value} readOnly style={{ ...inputStyle, background: 'rgba(255,255,255,0.03)' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Подключение CRM */}
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9' }}>Подключение CRM</h2>
            {crmStatus && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#2dd4bf', fontWeight: 600 }}>
                <CheckCircle size={14} /> {crmStatus.crm_type}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>Тип CRM</label>
              <select value={crmType} onChange={(e) => setCrmType(e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }}>
                <option value="mock">Демо-данные (без CRM)</option>
                <option value="amocrm">amoCRM</option>
              </select>
            </div>

            {crmType === 'amocrm' && (
              <>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>Поддомен (example.amocrm.ru)</label>
                  <input value={subdomain} onChange={(e) => setSubdomain(e.target.value)} placeholder="example" style={inputStyle} />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>Access Token</label>
                  <input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Токен из настроек amoCRM" style={inputStyle} />
                </div>
              </>
            )}

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 14, background: 'rgba(251,146,60,0.1)', borderRadius: 10, border: '1px solid rgba(251,146,60,0.2)' }}>
              <input type="checkbox" id="consent" checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 2 }} />
              <label htmlFor="consent" style={{ fontSize: 12, color: '#fb923c', lineHeight: 1.5, cursor: 'pointer' }}>
                Подтверждаю, что получены все необходимые согласия сотрудников на обработку персональных данных.
              </label>
            </div>

            <button
              onClick={() => connectMutation.mutate()}
              disabled={connectMutation.isPending || (crmType !== 'mock' && !consent)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '12px', background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)', color: '#fff', border: 'none',
                borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer',
                opacity: (connectMutation.isPending || (crmType !== 'mock' && !consent)) ? 0.6 : 1,
              }}
            >
              <Plug size={16} />
              {connectMutation.isPending ? 'Подключение...' : 'Подключить CRM'}
            </button>
          </div>
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
            <div style={{ padding: '12px 14px', background: 'rgba(45,212,191,0.1)', borderRadius: 10, fontSize: 13, color: '#2dd4bf', border: '1px solid rgba(45,212,191,0.2)' }}>
              ✅ Ваш Telegram-аккаунт привязан. Открывайте Sellex прямо из бота — авторизация автоматическая.
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <a
                href={miniAppUrl || botLink}
                target="_blank" rel="noreferrer"
                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '11px', background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)', color: '#fff', borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}
              >
                <Send size={15} /> Открыть в Telegram
              </a>
              <button
                onClick={() => unlinkTgMutation.mutate()}
                disabled={unlinkTgMutation.isPending}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '11px 14px', background: 'rgba(244,114,182,0.1)', color: '#f472b6', border: '1px solid rgba(244,114,182,0.25)', borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer' }}
              >
                <Unlink size={15} /> Отвязать
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: 10, fontSize: 13, color: '#94a3b8', lineHeight: 1.6, border: '1px solid rgba(255,255,255,0.07)' }}>
              <strong>Как привязать аккаунт:</strong>
              <ol style={{ margin: '8px 0 0 16px', padding: 0 }}>
                <li>Откройте бота Sellex в Telegram</li>
                <li>Нажмите кнопку «Открыть приложение»</li>
                <li>Введите ваш email и пароль от Sellex</li>
                <li>Аккаунты будут связаны автоматически</li>
              </ol>
            </div>
            <a
              href={botLink}
              target="_blank" rel="noreferrer"
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '12px', background: 'linear-gradient(135deg, #2dd4bf 0%, #a78bfa 100%)', color: '#fff', borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}
            >
              <Send size={16} /> Перейти к боту Sellex
            </a>
          </div>
        )}
      </div>

      <div style={{ marginTop: 20, padding: '12px 16px', background: 'rgba(244,114,182,0.1)', borderRadius: 10, fontSize: 12, color: '#f472b6', border: '1px solid rgba(244,114,182,0.25)' }}>
        ⚠️ Все аналитические выводы системы носят рекомендательный характер. Система является обработчиком данных — ответственность оператора несёт компания-клиент.
      </div>
    </div>
  );
}
