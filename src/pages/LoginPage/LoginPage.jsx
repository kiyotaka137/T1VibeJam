import React, { useState } from "react";
import { Code, LogIn, UserPlus, Loader2 } from "lucide-react";
import { useAuth } from "../../app/providers/AuthContext.jsx";

export function LoginPage({ onLogin }) {
  const auth = useAuth();

  const [mode, setMode] = useState("login");
  const isRegister = mode === "signup";

  const [name, setName] = useState("");
  const [role, setRole] = useState("hr");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const validate = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return "Введите корректный Email";
    if (!password || password.length < 6) return "Пароль минимум 6 символов";
    if (isRegister) {
      if (!name.trim()) return "Введите имя";
      if (!["hr", "candidate"].includes(role)) return "Некорректная роль";
    }
    return "";
  };

  const submit = async () => {
    const msg = validate();
    if (msg) {
      setError(msg);
      return;
    }

    try {
      setError("");
      setLoading(true);

      if (isRegister) {
        // Реальный запрос через Context
        await auth.signup({
          email: email.trim().toLowerCase(),
          password,
          name: name.trim(),
          role,
        });
      } else {
        // Реальный запрос через Context
        await auth.login(email.trim().toLowerCase(), password);
      }

      // Если ошибок не было, вызываем коллбек перехода
      if (onLogin) onLogin();

    } catch (e) {
      console.error(e);
      // Если сервер упал, e.message может быть 'Failed to fetch'
      setError(e.message === 'Failed to fetch' ? 'Нет соединения с сервером' : e.message);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center font-sans">
      <div className="bg-slate-800 p-8 rounded-xl shadow-2xl w-96 border border-slate-700">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
            <Code className="text-white w-8 h-8" />
          </div>
        </div>

        <h2 className="text-2xl font-bold text-white text-center mb-2">
          {isRegister ? "Регистрация" : "Вход"}
        </h2>
        <p className="text-center text-slate-400 text-sm mb-6">
          {isRegister ? "Создайте аккаунт" : "Войдите в систему"}
        </p>

        {isRegister && (
          <>
            <label className="block text-xs text-slate-400 mb-1">Имя</label>
            <input
              type="text"
              placeholder="Например: Alice HR"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full mb-4 p-3 rounded bg-slate-700 text-white border border-slate-600 focus:border-blue-500 outline-none"
            />

            <label className="block text-xs text-slate-400 mb-1">Роль</label>
            <select
              className="w-full mb-4 p-3 rounded bg-slate-700 text-white border border-slate-600 focus:border-blue-500 outline-none"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="hr">HR</option>
              <option value="candidate">Candidate</option>
            </select>
          </>
        )}

        <label className="block text-xs text-slate-400 mb-1">Email</label>
        <input
          type="email"
          placeholder="hr1@test.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={`w-full mb-4 p-3 rounded bg-slate-700 text-white border outline-none ${
            error ? "border-red-500" : "border-slate-600 focus:border-blue-500"
          }`}
        />

        <label className="block text-xs text-slate-400 mb-1">Пароль</label>
        <input
          type="password"
          placeholder="secret123"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={onKeyDown}
          className={`w-full mb-2 p-3 rounded bg-slate-700 text-white border outline-none ${
            error ? "border-red-500" : "border-slate-600 focus:border-blue-500"
          }`}
        />

        {error && (
          <div className="mt-2 mb-4 text-sm text-red-300 bg-red-950/40 border border-red-900 rounded p-3">
            {error}
          </div>
        )}

        <button
          onClick={submit}
          disabled={loading}
          className={`w-full font-bold py-3 rounded transition mb-4 flex items-center justify-center gap-2 ${
            loading
              ? "bg-blue-600/60 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-500"
          } text-white`}
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} /> Загрузка...
            </>
          ) : isRegister ? (
            "Зарегистрироваться"
          ) : (
            "Войти"
          )}
        </button>

        <button
          onClick={() => {
            setError("");
            setMode(isRegister ? "login" : "signup");
          }}
          className="w-full text-slate-400 hover:text-white text-sm flex items-center justify-center gap-2 transition"
        >
          {isRegister ? (
            <>
              <LogIn size={14} /> Уже есть аккаунт? Войти
            </>
          ) : (
            <>
              <UserPlus size={14} /> Нет аккаунта? Регистрация
            </>
          )}
        </button>
      </div>
    </div>
  );
}