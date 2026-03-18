'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      if (res.ok) {
        router.push('/');
        router.refresh();
      } else {
        const data = await res.json();
        setError(data.error || 'Invalid password');
      }
    } catch {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{
        margin: 0,
        background: '#0a0a0a',
        fontFamily: "'JetBrains Mono', monospace",
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        color: '#00ff88',
      }}>
        <div style={{
          border: '1px solid #00ff8844',
          borderRadius: 8,
          padding: '40px 36px',
          maxWidth: 380,
          width: '100%',
          background: '#111',
          boxShadow: '0 0 40px rgba(0,255,136,0.05)',
        }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 2 }}>📈 QUANTCLAW</div>
            <div style={{ fontSize: 12, color: '#00ff8888', marginTop: 6 }}>DATA TERMINAL — INTERNAL ACCESS</div>
          </div>

          <form onSubmit={handleSubmit}>
            <label style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 1 }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoFocus
              placeholder="Enter access code"
              style={{
                display: 'block',
                width: '100%',
                padding: '12px 14px',
                marginTop: 8,
                marginBottom: 16,
                background: '#0a0a0a',
                border: '1px solid #333',
                borderRadius: 4,
                color: '#00ff88',
                fontSize: 15,
                fontFamily: "'JetBrains Mono', monospace",
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />

            {error && (
              <div style={{ color: '#ff4444', fontSize: 13, marginBottom: 12 }}>{error}</div>
            )}

            <button
              type="submit"
              disabled={loading || !password}
              style={{
                width: '100%',
                padding: '12px 0',
                background: loading ? '#333' : '#00ff88',
                color: '#0a0a0a',
                border: 'none',
                borderRadius: 4,
                fontSize: 14,
                fontWeight: 700,
                fontFamily: "'JetBrains Mono', monospace",
                cursor: loading ? 'wait' : 'pointer',
                letterSpacing: 1,
              }}
            >
              {loading ? 'AUTHENTICATING...' : 'ACCESS TERMINAL'}
            </button>
          </form>
        </div>
      </body>
    </html>
  );
}
