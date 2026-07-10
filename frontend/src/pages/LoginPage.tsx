import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';

export default function LoginPage({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('analyst@example.com');
  const [password, setPassword] = useState('valid_password');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await authApi.login(email, password);
      localStorage.setItem('token', data.access_token);
      onSuccess();
      navigate('/dashboard');
    } catch {
      setError('Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-brand">
        <div className="eyebrow">Система бюджетирования</div>
        <h1 className="mark">СВОД</h1>
        <p className="lead">
          Быстрый пересчёт сценариев бюджета строительных объектов.
          Консолидация, сравнение версий и отчёты — вместо часов в Excel.
        </p>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <h2>Вход в систему</h2>
          <p>Демонстрационный контур для менеджмента и аналитиков</p>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          </div>
          <div className="field">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Входим…' : 'Войти'}
          </button>
          <div className="hint">
            Демо: analyst@example.com / valid_password
          </div>
        </form>
      </section>
    </div>
  );
}
