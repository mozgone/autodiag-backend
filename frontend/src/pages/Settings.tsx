import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCRMStatus, connectCRM } from '../api/client';
import { useAuthStore } from '../store/auth';
import toast from 'react-hot-toast';
import { CheckCircle, Plug } from 'lucide-react';

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const { data: crmStatus } = useQuery({ queryKey: ['crm-status'], queryFn: getCRMStatus });
  const [crmType, setCrmType] = useState('mock');
  const [subdomain, setSubdomain] = useState('');
  const [token, setToken] = useState('');
  const [consent, setConsent] = useState(false);
  const queryClient = useQueryClient();

  const connectMutation = useMutation({
    mutationFn: () => connectCRM({ crm_type: crmType, subdomain, access_token: token }),
    onSuccess: () => {
      toast.success('CRM успешно подключена!');
      queryClient.invalidateQueries({ queryKey: ['crm-status'] });
    },
    onError: () => toast.error('Ошибка подключения CRM'),
  });

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '11px 14px', border: '1.5px solid #e2e8f0',
    borderRadius: 10, fontSize: 14, outline: 'none',
  };
  const card: React.CSSProperties = {
    background: '#fff', borderRadius: 16, padding: 28, border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.07)',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>Настройки</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>Управление аккаунтом и подключение CRM</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Профиль */}
        <div style={card}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: '#1e293b' }}>Профиль</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Имя', value: user?.full_name || '' },
              { label: 'Email', value: user?.email || '' },
              { label: 'Роль', value: user?.role || '' },
            ].map(({ label, value }) => (
              <div key={label}>
                <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>{label}</label>
                <input value={value} readOnly style={{ ...inputStyle, background: '#f8fafc' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Подключение CRM */}
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b' }}>Подключение CRM</h2>
            {crmStatus && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#10b981', fontWeight: 600 }}>
                <CheckCircle size={14} /> {crmStatus.crm_type}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 6 }}>Тип CRM</label>
              <select value={crmType} onChange={(e) => setCrmType(e.target.value)} style={inputStyle}>
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

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 14, background: '#fef3c7', borderRadius: 10 }}>
              <input type="checkbox" id="consent" checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 2 }} />
              <label htmlFor="consent" style={{ fontSize: 12, color: '#92400e', lineHeight: 1.5, cursor: 'pointer' }}>
                Подтверждаю, что получены все необходимые согласия сотрудников на обработку персональных данных.
              </label>
            </div>

            <button
              onClick={() => connectMutation.mutate()}
              disabled={connectMutation.isPending || (crmType !== 'mock' && !consent)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '12px', background: '#6366f1', color: '#fff', border: 'none',
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

      <div style={{ marginTop: 20, padding: '12px 16px', background: '#fef2f2', borderRadius: 10, fontSize: 12, color: '#991b1b', border: '1px solid #fecaca' }}>
        ⚠️ Все аналитические выводы системы носят рекомендательный характер. Система является обработчиком данных — ответственность оператора несёт компания-клиент.
      </div>
    </div>
  );
}
