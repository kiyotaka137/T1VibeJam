import React, { useMemo, useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  GripHorizontal,
  Lightbulb,
  Lock,
  LogOut,
  MessageSquare,
  Play,
  Send,
  ShieldAlert,
  Loader2
} from "lucide-react";
import { api } from "../../services/api";

import { EDITOR_LANGUAGES, DISPLAY_LANGUAGES, LANGUAGE_TEMPLATES } from "../../shared/constants/languages.js";
import { INTERVIEW_TASKS } from "../../shared/mock/interviewTasks.js";
import { formatMMSS } from "../../shared/lib/time.js";
import { useMainTimer } from "./hooks/useMainTimer.js";
import { useResizablePanel } from "./hooks/useResizablePanel.js";

export function InterviewRoom({ onExit, inviteToken }) {
  // --- Initialization Logic ---
  const [isValidating, setIsValidating] = useState(!!inviteToken);
  const [initError, setInitError] = useState(null);
  const [interviewData, setInterviewData] = useState(null);

  // --- Core State ---
  const [taskIndex, setTaskIndex] = useState(0);
  const [language, setLanguage] = useState("javascript");
  const [code, setCode] = useState(LANGUAGE_TEMPLATES["javascript"]);
  const [leftTab, setLeftTab] = useState("task");

  const [testStatus, setTestStatus] = useState("idle");
  const [hiddenProgress, setHiddenProgress] = useState(0);

  const [messages, setMessages] = useState([
    { sender: "ai", text: "Здравствуйте! Я ваш AI-интервьюер. Давайте начнем." },
  ]);
  const [inputMsg, setInputMsg] = useState("");

  // --- STATE: ANTI-CHEAT ---
  const [disqualified, setDisqualified] = useState(false);
  const [disqReason, setDisqReason] = useState("");
  const [cheatWarning, setCheatWarning] = useState(false);
  const [timerCount, setTimerCount] = useState(3);
  const timerRef = useRef(null);

  const [finished, setFinished] = useState(false);

  // 1. При старте: Проверяем токен и Клеймим инвайт
  useEffect(() => {
    if (!inviteToken) return;

    const startSession = async () => {
      try {
        setIsValidating(true);
        // 1. Preview
        const preview = await api.get(`/v1/invites/${inviteToken}`);
        if (!preview.valid) throw new Error("Инвайт истёк или недействителен");

        // 2. Claim (Simulate candidate login first if needed, here we just call claim)
        // Для теста считаем, что кандидат авторизован. Если нет - тут нужно кидать на логин кандидата.
        // Для демо "Claim" делаем от текущего юзера (mock).
        localStorage.setItem("auth_token", "mock_candidate_jwt"); 
        
        const claim = await api.post(`/v1/invites/${inviteToken}/claim`);
        
        // Объединяем данные превью и клейма
        setInterviewData({
            ...claim,
            level: preview.interview_preview?.level || "middle",
            topics: preview.interview_preview?.topics || []
        });

      } catch (e) {
        setInitError(e.message);
      } finally {
        setIsValidating(false);
      }
    };

    startSession();
  }, [inviteToken]);

  // Фильтруем задачи на основе уровня из API
  const filteredTasks = useMemo(() => {
    // Если демо (нет токена) или данные еще не загружены - показываем все или дефолт
    if (!inviteToken) return INTERVIEW_TASKS;
    if (!interviewData) return [];

    // Ищем задачи совпадающие по уровню
    const level = interviewData.level.toLowerCase();
    const tasks = INTERVIEW_TASKS.filter(t => t.difficulty.toLowerCase() === level);
    
    return tasks.length > 0 ? tasks : INTERVIEW_TASKS.slice(0, 2); // Fallback
  }, [interviewData, inviteToken]);

  const currentTask = useMemo(() => filteredTasks[taskIndex] || {}, [filteredTasks, taskIndex]);

  const paused = finished || disqualified || isValidating;
  const { timeLeft, timedOut } = useMainTimer({ initialSeconds: 3600, paused });

  const { height: outputHeight, startResizing } = useResizablePanel({ initialHeight: 250 });

  // --- ЛОГИКА ЦВЕТОВ СЛОЖНОСТИ ---
  const getDifficultyColor = (difficulty) => {
    const diff = difficulty?.toLowerCase() || "";
    
    if (diff === "junior" || diff === "easy") {
      return "bg-green-900 text-green-300 border border-green-700";
    }
    if (diff === "middle" || diff === "medium") {
      return "bg-yellow-900 text-yellow-300 border border-yellow-700";
    }
    if (diff === "senior" || diff === "hard") {
      return "bg-red-900 text-red-300 border border-red-700";
    }
    return "bg-slate-800 text-slate-400 border border-slate-600";
  };

  // --- ЛОГИКА АНТИ-ЧИТА ---
  useEffect(() => {
    if (finished || disqualified || timedOut || isValidating) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setDisqualified(true);
        setDisqReason("Вы свернули окно или переключили вкладку. Собеседование прекращено.");
      }
    };

    const handleMouseLeave = () => {
      setCheatWarning(true);
      setTimerCount(3);

      if (timerRef.current) clearInterval(timerRef.current);

      timerRef.current = setInterval(() => {
        setTimerCount((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setDisqualified(true);
            setDisqReason("Курсор находился вне рабочей области более 3 секунд.");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    };

    const handleMouseEnter = () => {
      setCheatWarning(false);
      setTimerCount(3);
      if (timerRef.current) clearInterval(timerRef.current);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.body.addEventListener("mouseleave", handleMouseLeave);
    document.body.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [finished, disqualified, timedOut, isValidating]);


  const handleLanguageChange = (e) => {
    const lang = e.target.value;
    setLanguage(lang);
    setCode(LANGUAGE_TEMPLATES[lang] || "// Code here");
  };

  const handleRun = () => {
    setTestStatus("running");
    setTimeout(() => setTestStatus("passed_visible"), 900);
  };

  const handleSubmit = () => {
    setTestStatus("running");

    setTimeout(() => {
      setTestStatus("passed_visible");

      setTimeout(() => {
        setTestStatus("checking_hidden");
        setHiddenProgress(0);

        const progressInterval = setInterval(() => {
          setHiddenProgress((prev) => (prev >= 100 ? 100 : prev + 5));
        }, 80);

        setTimeout(() => {
          clearInterval(progressInterval);
          setHiddenProgress(100);
          setTestStatus("passed_all");

          setTimeout(() => {
            if (taskIndex < filteredTasks.length - 1) {
              setTaskIndex((p) => p + 1);
              setTestStatus("idle");
              setCode(LANGUAGE_TEMPLATES[language]);
              setMessages((prev) => [...prev, { sender: "ai", text: "Отлично! Переходим к следующей задаче." }]);
              setHiddenProgress(0);
            } else {
              setFinished(true);
            }
          }, 1200);
        }, 1800);
      }, 700);
    }, 900);
  };

  const preventCopyPaste = (e) => {
    e.preventDefault();
    alert("Копирование и вставка запрещены правилами собеседования.");
  };

  const sendChat = () => {
    const text = inputMsg.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { sender: "me", text }]);
    setInputMsg("");
  };

  if (isValidating) {
    return (
      <div className="h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <Loader2 className="animate-spin mb-4" size={48} />
        <h2 className="text-xl">Подготовка окружения...</h2>
      </div>
    );
  }

  if (initError) {
    return (
      <div className="h-screen bg-slate-950 flex flex-col items-center justify-center text-red-400 p-10 text-center">
        <ShieldAlert size={64} className="mb-4" />
        <h2 className="text-2xl font-bold mb-2">Ошибка доступа</h2>
        <p className="mb-6">{initError}</p>
        <button onClick={onExit} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700">
          Вернуться на главную
        </button>
      </div>
    );
  }

  if (disqualified) {
    return (
      <div className="h-screen bg-red-950 flex flex-col items-center justify-center text-center p-10 font-sans relative z-50">
        <ShieldAlert size={80} className="text-red-500 mb-6" />
        <h1 className="text-4xl text-white font-bold mb-4">Собеседование прекращено</h1>
        <p className="text-xl text-red-200 mb-8 max-w-xl">
          Нарушение: <br />
          <span className="font-bold">{disqReason}</span>
        </p>
        <button
          onClick={onExit}
          className="bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded font-bold transition"
        >
          Вернуться
        </button>
      </div>
    );
  }

  if (timedOut) {
    return (
      <div className="h-screen bg-slate-900 flex flex-col items-center justify-center text-center p-10 font-sans relative z-50">
        <Clock size={80} className="text-orange-500 mb-6" />
        <h1 className="text-4xl text-white font-bold mb-4">Время вышло</h1>
        <p className="text-xl text-slate-300 mb-8 max-w-xl">
          Вы не уложились в отведенное время.
        </p>
        <button
          onClick={onExit}
          className="bg-orange-600 hover:bg-orange-500 text-white px-8 py-3 rounded font-bold transition"
        >
          Вернуться
        </button>
      </div>
    );
  }
  
  // Safety check if tasks are empty
  if (!currentTask || !currentTask.title) {
     return <div className="h-screen bg-slate-950 text-white flex items-center justify-center">Нет задач для этого уровня</div>;
  }

  return (
    <div
      className="h-screen flex flex-col bg-slate-950 text-slate-300 overflow-hidden font-mono relative select-none"
      onContextMenu={(e) => e.preventDefault()}
      onCopy={preventCopyPaste}
      onCut={preventCopyPaste}
      onPaste={preventCopyPaste}
    >
      {cheatWarning && (
        <div className="absolute inset-0 z-50 bg-red-900/95 flex flex-col items-center justify-center backdrop-blur-sm">
          <AlertTriangle size={100} className="text-white mb-6 animate-bounce" />
          <h2 className="text-5xl font-bold text-white text-center mb-4">ВЕРНИТЕ КУРСОР!</h2>
          <p className="text-red-200 text-2xl font-bold">
            Блокировка через: <span className="text-white text-4xl">{timerCount}</span>
          </p>
        </div>
      )}

      {finished && (
        <div className="absolute inset-0 z-50 bg-slate-900/95 flex flex-col items-center justify-center backdrop-blur-sm">
          <div className="bg-slate-800 p-10 rounded-2xl border border-green-500/30 text-center shadow-2xl max-w-lg">
            <div className="w-20 h-20 bg-green-900/50 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500">
              <CheckCircle2 className="text-green-400 w-10 h-10" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Вы успешно сдали задачи!</h2>
            <p className="text-slate-300 mb-8">Все тесты (видимые и скрытые) пройдены.</p>
            <button
              onClick={onExit}
              className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded transition"
            >
              Выйти
            </button>
          </div>
        </div>
      )}

      <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <span className="font-bold text-white text-lg font-sans">VibeCode Jam</span>
          <span
            className={`bg-slate-800 text-xs px-2 py-1 rounded border ${
              timeLeft < 300 ? "border-red-500 text-red-400 animate-pulse" : "border-slate-700 text-slate-400"
            } flex items-center gap-2`}
          >
            <Clock size={12} /> {formatMMSS(timeLeft)}
          </span>
          <span className="text-xs text-slate-500">
            Task {taskIndex + 1}/{filteredTasks.length}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRun}
            disabled={testStatus === "running"}
            className="bg-emerald-700 hover:bg-emerald-600 px-3 py-1.5 rounded text-sm text-white flex items-center gap-2 transition font-medium"
          >
            <Play size={14} /> Run
          </button>

          <button
            onClick={handleSubmit}
            disabled={testStatus !== "passed_visible"}
            className={`${
              testStatus === "passed_visible"
                ? "bg-green-600 hover:bg-green-500"
                : "bg-slate-700 opacity-50 cursor-not-allowed"
            } px-4 py-1.5 rounded text-sm text-white font-bold flex items-center gap-2 transition`}
          >
            Submit <ChevronRight size={14} />
          </button>

          <div className="h-6 w-px bg-slate-700 mx-2"></div>

          <button
            onClick={onExit}
            className="bg-red-900/50 hover:bg-red-600/80 text-red-200 hover:text-white px-3 py-1.5 rounded text-sm flex items-center gap-2 transition border border-red-900"
          >
            <LogOut size={14} /> Exit
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* LEFT */}
        <div className="w-5/12 border-r border-slate-800 flex flex-col bg-slate-900">
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setLeftTab("task")}
              className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
                leftTab === "task"
                  ? "bg-slate-800 text-white border-b-2 border-blue-500"
                  : "text-slate-500 hover:bg-slate-800"
              }`}
            >
              <FileText size={16} /> Описание
            </button>
            <button
              onClick={() => setLeftTab("chat")}
              className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
                leftTab === "chat"
                  ? "bg-slate-800 text-white border-b-2 border-blue-500"
                  : "text-slate-500 hover:bg-slate-800"
              }`}
            >
              <MessageSquare size={16} /> AI Чат
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {leftTab === "task" ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-white text-xl m-0">{currentTask.title}</h2>
                  
                  {/* ОБНОВЛЕННАЯ ПЛАШКА СЛОЖНОСТИ */}
                  <span
                    className={`text-xs px-2 py-1 rounded uppercase font-bold ${getDifficultyColor(
                      currentTask.difficulty
                    )}`}
                  >
                    {currentTask.difficulty}
                  </span>
                </div>
                <p>{currentTask.description}</p>
                <div className="bg-slate-950 p-3 rounded border border-slate-800 mt-4">
                  <pre className="text-sm font-mono whitespace-pre-wrap">{currentTask.example}</pre>
                </div>
              </div>
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex-1 space-y-4 mb-4 overflow-y-auto custom-scrollbar">
                  {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.sender === "me" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[85%] p-3 rounded-lg text-sm ${
                          msg.sender === "me" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-200"
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-slate-800 pt-3">
                  <button
                    onClick={() =>
                      setMessages((prev) => [
                        ...prev,
                        { sender: "ai", text: "Подсказка: попробуйте использовать хеш-таблицу для O(1) поиска." },
                      ])
                    }
                    className="mb-3 w-full bg-slate-800 hover:bg-slate-700 text-yellow-500 text-xs py-2 rounded flex items-center justify-center gap-2 border border-slate-700 transition"
                  >
                    <Lightbulb size={12} /> Подсказка
                  </button>

                  <div className="flex gap-2">
                    <input
                      value={inputMsg}
                      onChange={(e) => setInputMsg(e.target.value)}
                      type="text"
                      className="flex-1 bg-slate-950 border border-slate-700 rounded p-2 text-sm text-white outline-none"
                      placeholder="Сообщение..."
                      onKeyDown={(e) => (e.key === "Enter" ? sendChat() : null)}
                    />
                    <button onClick={sendChat} className="p-2 bg-blue-600 rounded text-white">
                      <Send size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT */}
        <div className="w-7/12 flex flex-col h-full relative">
          <div className="h-10 bg-slate-900 border-b border-slate-800 flex items-center px-4 justify-between shrink-0">
            <select
              value={language}
              onChange={handleLanguageChange}
              className="bg-transparent text-xs text-slate-300 outline-none border border-slate-700 rounded px-2 py-1 cursor-pointer hover:border-slate-500"
            >
              {EDITOR_LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  {DISPLAY_LANGUAGES[lang]}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 bg-slate-950 relative overflow-hidden">
            <Editor
              height="100%"
              theme="vs-dark"
              language={language}
              value={code}
              onChange={(value) => setCode(value ?? "")}
              loading={
                <div className="flex items-center justify-center h-full text-slate-500 gap-2">
                  <Loader2 className="animate-spin" /> Загрузка IDE...
                </div>
              }
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                automaticLayout: true,
                scrollBeyondLastLine: false,
              }}
            />
          </div>

          <div
            className="h-1 bg-slate-800 hover:bg-blue-500 cursor-row-resize flex items-center justify-center transition-colors"
            onMouseDown={startResizing}
          >
            <GripHorizontal size={12} className="text-slate-600" />
          </div>

          <div style={{ height: outputHeight }} className="bg-slate-900 flex flex-col transition-none">
            <div className="h-8 bg-slate-800 px-4 flex items-center justify-between border-b border-slate-700 shrink-0">
              <span className="text-xs font-bold text-slate-400 uppercase">Test Results</span>
              {testStatus !== "idle" && (
                <span className="text-xs animate-pulse text-blue-400">
                  {testStatus === "running"
                    ? "Compiling..."
                    : testStatus === "checking_hidden"
                    ? "Running Hidden Tests..."
                    : ""}
                </span>
              )}
            </div>

            <div className="flex-1 p-4 font-mono text-sm overflow-y-auto custom-scrollbar">
              {testStatus === "idle" && (
                <div className="space-y-3 opacity-50">
                  {currentTask.visibleTests?.map((test, idx) => (
                    <div key={idx} className="bg-slate-950 p-3 rounded border border-slate-800">
                      <div className="text-xs text-slate-500 mb-1">Case {idx + 1}</div>
                      <div>Input: {test.input}</div>
                      <div>Expected: {test.expected}</div>
                    </div>
                  ))}
                </div>
              )}

              {(testStatus === "passed_visible" || testStatus === "checking_hidden" || testStatus === "passed_all") && (
                <div className="space-y-3">
                  <div className="text-green-400 font-bold mb-2 flex items-center gap-2">
                    <CheckCircle2 size={16} /> Visible Tests Passed
                  </div>
                  {currentTask.visibleTests?.map((test, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950 p-3 rounded border border-green-900/50 flex justify-between items-center"
                    >
                      <div>
                        <div className="text-xs text-slate-500">Case {idx + 1}</div>
                        <div className="text-slate-300">Input: {test.input}</div>
                      </div>
                      <div className="text-green-500 font-bold text-xs bg-green-900/20 px-2 py-1 rounded">
                        Passed
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {testStatus === "checking_hidden" && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-blue-400 text-xs font-bold flex items-center gap-2">
                      <Lock size={12} /> Running Hidden Tests...
                    </span>
                    <span className="text-blue-400 text-xs">{hiddenProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-100 ease-linear"
                      style={{ width: `${hiddenProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {testStatus === "passed_all" && (
                <div className="mt-4 pt-4 border-t border-slate-800 fade-in-up">
                  <div className="flex items-center gap-2 text-green-400 font-bold mb-2">
                    <Lock size={16} /> Hidden Tests
                  </div>
                  <div className="bg-green-900/20 border border-green-800 p-3 rounded text-green-300 text-center">
                    Hidden Test Cases Passed! 🎉
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}