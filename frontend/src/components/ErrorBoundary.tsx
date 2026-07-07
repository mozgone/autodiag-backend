import React from 'react';

interface State { hasError: boolean; error: Error | null }

export default class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh', background: '#0f0f1a', display: 'flex',
          alignItems: 'center', justifyContent: 'center', padding: 24,
        }}>
          <div style={{
            background: '#1a1a2e', borderRadius: 16, padding: 32, maxWidth: 480,
            border: '1px solid rgba(244,114,182,0.3)', textAlign: 'center',
          }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
            <h2 style={{ color: '#f472b6', fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
              Произошла ошибка
            </h2>
            <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>
              {this.state.error?.message || 'Неизвестная ошибка'}
            </p>
            <button
              onClick={() => window.location.href = '/login'}
              style={{
                padding: '10px 24px', background: 'linear-gradient(135deg, #2dd4bf, #a78bfa)',
                color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Перезагрузить
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
