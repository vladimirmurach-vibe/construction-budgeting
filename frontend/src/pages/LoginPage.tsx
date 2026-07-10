import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { authApi } from '../api/client';

interface Props {
  onLogin: () => void;
}

export default function LoginPage({ onLogin }: Props) {
  const { register, handleSubmit } = useForm();
  const [error, setError] = useState('');

  const submit = async (data: { email: string; password: string }) => {
    try {
      const resp = await authApi.login(data.email, data.password);
      localStorage.setItem('token', resp.access_token);
      onLogin();
    } catch {
      setError('Неверный email или пароль');
    }
  };

  return (
    <div className="login-page">
      <div className="card login-card">
        <h2>Вход в систему</h2>
        <form onSubmit={handleSubmit(submit)}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" {...register('email')} required />
          </div>
          <div className="form-group">
            <label>Пароль</label>
            <input type="password" {...register('password')} required />
          </div>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          <button className="btn" type="submit">Войти</button>
        </form>
      </div>
    </div>
  );
}
