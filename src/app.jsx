import React, { useState, useEffect, useRef, useMemo } from "react";
import Editor from "@monaco-editor/react"; // ИМПОРТ РЕДАКТОРА
import {
  Terminal,
  Play,
  Send,
  FileText,
  MessageSquare,
  History,
  PlusCircle,
  Database,
  LogOut,
  ChevronRight,
  Code,
  Lightbulb,
  Filter,
  ArrowUpFromLine,
  UserPlus,
  LogIn,
  Tag,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Lock,
  Calendar,
  Trophy,
  Clock,
  GripHorizontal,
} from "lucide-react";

// --- КОНСТАНТЫ И ШАБЛОНЫ КОДА ---

const LANGUAGE_TEMPLATES = {
  javascript: `// Напишите решение здесь\nfunction solve(input) {\n  return input;\n}`,
  python: `# Write your solution here\ndef solve(input_data):\n    return input_data`,
  cpp: `// Write your solution here\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> solve(vector<int>& nums) {\n        return nums;\n    }\n};`,
  java: `// Write your solution here\nclass Solution {\n    public int[] solve(int[] nums) {\n        return nums;\n    }\n}`,
  go: `// Write your solution here\npackage main\n\nfunc solve(input []int) []int {\n    return input\n}`,
};

// Маппинг для красивого отображения в выпадающем списке
const DISPLAY_LANGUAGES = {
  javascript: "JavaScript",
  python: "Python",
  cpp: "C++",
  java: "Java",
  go: "Go",
};

const EDITOR_LANGUAGES = Object.keys(LANGUAGE_TEMPLATES);

// Задачи для симуляции потока
const INTERVIEW_TASKS = [
  {
    id: 1,
    title: "1. Two Sum",
    difficulty: "Easy",
    description:
      "Дан массив целых чисел `nums` и число `target`. Верните индексы двух чисел так, чтобы их сумма была равна `target`.",
    example: "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]",
    visibleTests: [
      { input: "[2, 7, 11, 15], 9", expected: "[0, 1]" },
      { input: "[3, 2, 4], 6", expected: "[1, 2]" },
    ],
  },
  {
    id: 2,
    title: "2. Longest Substring",
    difficulty: "Medium",
    description:
      "Найдите длину самой длинной подстроки без повторяющихся символов.",
    example:
      'Input: s = "abcabcbb"\nOutput: 3\nExplanation: The answer is "abc", with the length of 3.',
    visibleTests: [
      { input: '"abcabcbb"', expected: "3" },
      { input: '"bbbbb"', expected: "1" },
    ],
  },
];

// --- КОМПОНЕНТЫ СТРАНИЦ ---

// 1. Страница авторизации
const LoginPage = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const handleAuth = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Пожалуйста, введите корректный Email");
      return;
    }
    setError("");
    onLogin();
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center font-sans">
      <div className="bg-slate-800 p-8 rounded-xl shadow-2xl w-96 border border-slate-700">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
            <Code className="text-white w-8 h-8" />
          </div>
        </div>
        <h2 className="text-2xl font-bold text-white text-center mb-6">
          {isRegister ? "Регистрация HR" : "HR Портал"}
        </h2>

        {isRegister && (
          <input
            type="text"
            placeholder="ФИО"
            className="w-full mb-4 p-3 rounded bg-slate-700 text-white border border-slate-600 focus:border-blue-500 outline-none"
          />
        )}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={`w-full mb-4 p-3 rounded bg-slate-700 text-white border outline-none ${
            error ? "border-red-500" : "border-slate-600 focus:border-blue-500"
          }`}
        />
        {error && <p className="text-red-400 text-xs mb-4">{error}</p>}

        <input
          type="password"
          placeholder="Пароль"
          className="w-full mb-4 p-3 rounded bg-slate-700 text-white border border-slate-600 focus:border-blue-500 outline-none"
        />

        {isRegister && (
          <input
            type="password"
            placeholder="Повторите пароль"
            className="w-full mb-6 p-3 rounded bg-slate-700 text-white border border-slate-600 focus:border-blue-500 outline-none"
          />
        )}

        <button
          onClick={handleAuth}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded transition mb-4"
        >
          {isRegister ? "Зарегистрироваться" : "Войти"}
        </button>

        <button
          onClick={() => {
            setIsRegister(!isRegister);
            setError("");
          }}
          className="w-full text-slate-400 hover:text-white text-sm flex items-center justify-center gap-2 transition"
        >
          {isRegister ? (
            <>
              <LogIn size={14} /> Войти
            </>
          ) : (
            <>
              <UserPlus size={14} /> Регистрация
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// 2. HR Панель
const HRDashboard = ({ onNavigateToInterview, onLogout }) => {
  const [activeTab, setActiveTab] = useState("create");
  const [generatedLink, setGeneratedLink] = useState("");
  const [interviewDifficulty, setInterviewDifficulty] = useState("Easy");

  // --- STATE: History ---
  const [historyFilterStatus, setHistoryFilterStatus] = useState("all");
  const [historySort, setHistorySort] = useState("dateDesc");

  const historyData = [
    {
      id: 1,
      candidate: "Alexey I.",
      date: "2023-11-24",
      score: 85,
      status: "Completed",
    },
    {
      id: 2,
      candidate: "Maria S.",
      date: "2023-11-25",
      score: 92,
      status: "Hire",
    },
    {
      id: 3,
      candidate: "John D.",
      date: "2023-11-20",
      score: 45,
      status: "Rejected",
    },
    {
      id: 4,
      candidate: "Ivan P.",
      date: "2023-11-26",
      score: 78,
      status: "Review",
    },
  ];

  const filteredHistory = useMemo(() => {
    let result = [...historyData];
    if (historyFilterStatus !== "all") {
      result = result.filter((item) => item.status === historyFilterStatus);
    }
    result.sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      if (historySort === "dateDesc") return dateB - dateA;
      if (historySort === "dateAsc") return dateA - dateB;
      if (historySort === "scoreDesc") return b.score - a.score;
      if (historySort === "scoreAsc") return a.score - b.score;
      return 0;
    });
    return result;
  }, [historyFilterStatus, historySort]);

  // --- STATE: Bank ---
  const [bankFilterDifficulty, setBankFilterDifficulty] = useState("All");
  const [bankFilterTag, setBankFilterTag] = useState("All");
  const [manualTask, setManualTask] = useState({
    condition: "",
    tests: "",
    difficulty: "Easy",
    tags: "",
  });

  const [tasksData, setTasksData] = useState([
    {
      id: 1,
      title: "Two Sum",
      difficulty: "Easy",
      tags: ["Array", "Hash Table"],
    },
    {
      id: 2,
      title: "LRU Cache",
      difficulty: "Hard",
      tags: ["Design", "Linked List"],
    },
    {
      id: 3,
      title: "Valid Parentheses",
      difficulty: "Easy",
      tags: ["Stack", "String"],
    },
    {
      id: 4,
      title: "Merge Intervals",
      difficulty: "Medium",
      tags: ["Array", "Sorting"],
    },
    {
      id: 5,
      title: "Network Delay Time",
      difficulty: "Medium",
      tags: ["Graph", "BFS"],
    },
  ]);

  const handleAddTask = () => {
    const newTags = manualTask.tags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t);
    const newTask = {
      id: Date.now(),
      title: "Новая задача (Manual)",
      difficulty: manualTask.difficulty,
      tags: newTags.length > 0 ? newTags : ["General"],
    };
    setTasksData([newTask, ...tasksData]);
    setManualTask({ condition: "", tests: "", difficulty: "Easy", tags: "" });
  };

  const allTags = useMemo(() => {
    const tags = new Set();
    tasksData.forEach((task) => task.tags.forEach((t) => tags.add(t)));
    return ["All", ...Array.from(tags).sort()];
  }, [tasksData]);

  const filteredTasks = tasksData.filter((task) => {
    const matchDiff =
      bankFilterDifficulty === "All" ||
      task.difficulty === bankFilterDifficulty;
    const matchTag =
      bankFilterTag === "All" || task.tags.includes(bankFilterTag);
    return matchDiff && matchTag;
  });

  const generateLink = () => {
    const uniqueId = Math.random().toString(36).substring(7);
    setGeneratedLink(
      `https://vibecode.io/interview/${uniqueId}?diff=${interviewDifficulty}`
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex font-sans">
      <div className="w-64 bg-slate-900 text-white p-6 flex flex-col shrink-0">
        <h1 className="text-xl font-bold mb-10 flex items-center gap-2">
          <Code /> VibeJam HR
        </h1>
        <nav className="flex-1 space-y-4">
          <button
            onClick={() => setActiveTab("create")}
            className={`w-full flex items-center gap-3 p-3 rounded transition ${
              activeTab === "create" ? "bg-blue-600" : "hover:bg-slate-800"
            }`}
          >
            <PlusCircle size={20} /> Создать интервью
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`w-full flex items-center gap-3 p-3 rounded transition ${
              activeTab === "history" ? "bg-blue-600" : "hover:bg-slate-800"
            }`}
          >
            <History size={20} /> История
          </button>
          <button
            onClick={() => setActiveTab("bank")}
            className={`w-full flex items-center gap-3 p-3 rounded transition ${
              activeTab === "bank" ? "bg-blue-600" : "hover:bg-slate-800"
            }`}
          >
            <Database size={20} /> Банк задач
          </button>
        </nav>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 text-slate-400 hover:text-white mt-auto transition"
        >
          <LogOut size={18} /> Выход
        </button>
      </div>

      <div className="flex-1 p-10 overflow-y-auto">
        {activeTab === "create" && (
          <div className="bg-white p-8 rounded-xl shadow-sm max-w-2xl border border-gray-100">
            <h2 className="text-2xl font-bold mb-6 text-slate-800">
              Новое собеседование
            </h2>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-600 mb-2">
                  Сложность
                </label>
                <select
                  className="w-full p-3 border rounded-lg bg-gray-50 outline-none"
                  value={interviewDifficulty}
                  onChange={(e) => setInterviewDifficulty(e.target.value)}
                >
                  <option>Easy</option>
                  <option>Medium</option>
                  <option>Hard</option>
                </select>
              </div>
              <button
                onClick={generateLink}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition"
              >
                Сгенерировать ссылку
              </button>
              {generatedLink && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
                  <span className="text-green-800 font-mono text-sm">
                    {generatedLink}
                  </span>
                  <button
                    onClick={onNavigateToInterview}
                    className="text-sm bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                  >
                    Перейти (Demo)
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "bank" && (
          <div className="grid grid-cols-2 gap-6 h-[650px]">
            <div className="flex flex-col gap-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-lg mb-4 text-slate-800 flex items-center gap-2">
                  <ArrowUpFromLine size={18} /> Добавить задачу
                </h3>
                <div className="space-y-3">
                  <textarea
                    className="w-full p-2 border rounded bg-gray-50 text-sm h-16 outline-none resize-none"
                    placeholder="Условие задачи..."
                    value={manualTask.condition}
                    onChange={(e) =>
                      setManualTask({
                        ...manualTask,
                        condition: e.target.value,
                      })
                    }
                  />
                  <textarea
                    className="w-full p-2 border rounded bg-gray-50 text-sm h-16 font-mono outline-none resize-none"
                    placeholder='JSON тесты: [{"input": "...", "output": "..."}]'
                    value={manualTask.tests}
                    onChange={(e) =>
                      setManualTask({ ...manualTask, tests: e.target.value })
                    }
                  />
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="flex-1 p-2 border rounded bg-gray-50 text-sm"
                      placeholder="Теги (Array, DP...)"
                      value={manualTask.tags}
                      onChange={(e) =>
                        setManualTask({ ...manualTask, tags: e.target.value })
                      }
                    />
                    <select
                      className="w-1/3 p-2 border rounded bg-gray-50 text-sm"
                      value={manualTask.difficulty}
                      onChange={(e) =>
                        setManualTask({
                          ...manualTask,
                          difficulty: e.target.value,
                        })
                      }
                    >
                      <option>Easy</option>
                      <option>Medium</option>
                      <option>Hard</option>
                    </select>
                  </div>
                  <button
                    onClick={handleAddTask}
                    className="w-full bg-slate-800 text-white py-2 rounded hover:bg-slate-700 text-sm"
                  >
                    Загрузить
                  </button>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex-1 overflow-hidden flex flex-col">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-slate-800">Банк задач</h3>
                  <div className="flex gap-2">
                    <select
                      className="text-xs border rounded p-1"
                      value={bankFilterDifficulty}
                      onChange={(e) => setBankFilterDifficulty(e.target.value)}
                    >
                      <option value="All">Diff: All</option>
                      <option value="Easy">Easy</option>
                      <option value="Medium">Medium</option>
                      <option value="Hard">Hard</option>
                    </select>
                    <select
                      className="text-xs border rounded p-1 max-w-[100px]"
                      value={bankFilterTag}
                      onChange={(e) => setBankFilterTag(e.target.value)}
                    >
                      {allTags.map((tag) => (
                        <option key={tag} value={tag}>
                          {tag === "All" ? "Tags: All" : tag}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <ul className="overflow-y-auto flex-1 pr-1 custom-scrollbar space-y-2">
                  {filteredTasks.map((task) => (
                    <li
                      key={task.id}
                      className="p-3 border rounded bg-gray-50 flex flex-col gap-2 hover:bg-gray-100 transition"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-slate-700 truncate max-w-[150px]">
                          {task.title}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold ${
                            task.difficulty === "Easy"
                              ? "bg-green-100 text-green-700"
                              : task.difficulty === "Medium"
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {task.difficulty}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {task.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="bg-slate-200 text-slate-600 text-[10px] px-1.5 rounded flex items-center gap-0.5"
                          >
                            <Tag size={8} /> {tag}
                          </span>
                        ))}
                      </div>
                    </li>
                  ))}
                  {filteredTasks.length === 0 && (
                    <div className="text-center text-slate-400 text-sm mt-4">
                      Задачи не найдены
                    </div>
                  )}
                </ul>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-slate-800">
                <Terminal size={18} /> Генератор (Scibox LLM)
              </h3>
              <div className="flex-1 bg-slate-900 rounded-lg p-4 mb-4 overflow-y-auto text-sm custom-scrollbar">
                <div className="mb-4">
                  <p className="text-blue-400 font-bold mb-1">Scibox AI:</p>
                  <p className="text-slate-300">
                    Опишите тему и уровень, я сгенерирую задачу.
                  </p>
                </div>
                <div className="mb-4 text-right">
                  <p className="text-green-400 font-bold mb-1">HR:</p>
                  <span className="bg-slate-800 px-3 py-2 rounded text-white inline-block">
                    Задача на жадные алгоритмы
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Запрос к AI..."
                  className="flex-1 p-2 border rounded bg-gray-50 outline-none"
                />
                <button className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "history" && (
          <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-slate-800">
                История собеседований
              </h2>
              <div className="flex gap-3">
                <select
                  className="p-2 border rounded text-sm bg-gray-50"
                  value={historyFilterStatus}
                  onChange={(e) => setHistoryFilterStatus(e.target.value)}
                >
                  <option value="all">Все статусы</option>
                  <option value="Completed">Completed</option>
                  <option value="Hire">Hire</option>
                  <option value="Rejected">Rejected</option>
                </select>
                <select
                  className="p-2 border rounded text-sm bg-gray-50"
                  value={historySort}
                  onChange={(e) => setHistorySort(e.target.value)}
                >
                  <option value="dateDesc">Дата: Сначала новые</option>
                  <option value="dateAsc">Дата: Сначала старые</option>
                  <option value="scoreDesc">Баллы: По убыванию</option>
                  <option value="scoreAsc">Баллы: По возрастанию</option>
                </select>
              </div>
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="border-b text-slate-500 text-sm uppercase">
                  <th className="pb-3 pl-2">Кандидат</th>
                  <th className="pb-3">Дата</th>
                  <th className="pb-3">Оценка</th>
                  <th className="pb-3">Статус</th>
                  <th className="pb-3">Действие</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistory.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b last:border-0 hover:bg-gray-50 transition"
                  >
                    <td className="py-4 pl-2 font-medium text-slate-700">
                      {item.candidate}
                    </td>
                    <td className="py-4 text-slate-600 flex items-center gap-1">
                      <Calendar size={14} /> {item.date}
                    </td>
                    <td className="py-4 text-blue-600 font-bold flex items-center gap-1">
                      <Trophy size={14} /> {item.score}/100
                    </td>
                    <td className="py-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          item.status === "Hire"
                            ? "bg-green-100 text-green-800"
                            : item.status === "Rejected"
                            ? "bg-red-100 text-red-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-4">
                      <button className="text-blue-500 hover:text-blue-700 text-sm font-medium">
                        Скачать отчет
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// 3. Интерфейс Кандидата (С Monaco Editor, Таймером, Анимацией тестов и Ресайзом)
const InterviewRoom = ({ onExit }) => {
  const [taskIndex, setTaskIndex] = useState(0);
  const [language, setLanguage] = useState("javascript");
  const [code, setCode] = useState(LANGUAGE_TEMPLATES["javascript"]);
  const [leftTab, setLeftTab] = useState("task");
  const [testStatus, setTestStatus] = useState("idle");
  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Здравствуйте! Я ваш AI-интервьюер. Давайте начнем.",
    },
  ]);
  const [inputMsg, setInputMsg] = useState("");

  // States: Anti-Cheat & Flow
  const [cheatWarning, setCheatWarning] = useState(false);
  const [timerCount, setTimerCount] = useState(3);
  const [disqualified, setDisqualified] = useState(false);
  const [disqReason, setDisqReason] = useState("");
  const [finished, setFinished] = useState(false);
  const [timeOut, setTimeOut] = useState(false);

  // State: Main Timer (1 hour = 3600 sec)
  const [timeLeft, setTimeLeft] = useState(3600);

  // State: Hidden Test Progress
  const [hiddenProgress, setHiddenProgress] = useState(0);

  // State: Output Window Height
  const [outputHeight, setOutputHeight] = useState(250);
  const [isResizing, setIsResizing] = useState(false);

  const currentTask = INTERVIEW_TASKS[taskIndex];
  const intervalRef = useRef(null);

  // --- LOGIC: MAIN TIMER ---
  useEffect(() => {
    if (timeLeft > 0 && !finished && !disqualified && !timeOut) {
      const timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    } else if (timeLeft === 0 && !finished && !disqualified) {
      setTimeOut(true);
    }
  }, [timeLeft, finished, disqualified, timeOut]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // --- LOGIC: RESIZING OUTPUT ---
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizing) {
        // Calculate new height based on mouse position from bottom
        const newHeight = window.innerHeight - e.clientY;
        if (newHeight > 100 && newHeight < window.innerHeight - 150) {
          setOutputHeight(newHeight);
        }
      }
    };
    const handleMouseUp = () => setIsResizing(false);

    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  // --- LOGIC: ANTI-CHEAT ---
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && !finished && !disqualified && !timeOut) {
        setDisqualified(true);
        setDisqReason("Переключение вкладки или сворачивание окна.");
      }
    };

    const handleMouseLeave = () => {
      if (finished || disqualified || timeOut) return;
      setCheatWarning(true);
      setTimerCount(3);
      intervalRef.current = setInterval(() => {
        setTimerCount((prev) => {
          if (prev <= 1) {
            clearInterval(intervalRef.current);
            setDisqualified(true);
            setDisqReason(
              "Курсор мыши находился вне рабочей области более 3 секунд."
            );
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    };

    const handleMouseEnter = () => {
      setCheatWarning(false);
      setTimerCount(3);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.body.addEventListener("mouseleave", handleMouseLeave);
    document.body.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [finished, disqualified, timeOut]);

  const handleLanguageChange = (e) => {
    const lang = e.target.value;
    setLanguage(lang);
    setCode(LANGUAGE_TEMPLATES[lang] || "// Code here");
  };

  const handleRun = () => {
    setTestStatus("running");
    setTimeout(() => setTestStatus("passed_visible"), 1500);
  };

  const handleSubmit = () => {
    setTestStatus("running");

    // 1. Visible Tests
    setTimeout(() => {
      setTestStatus("passed_visible");

      // 2. Hidden Tests Start
      setTimeout(() => {
        setTestStatus("checking_hidden");
        setHiddenProgress(0);

        // ANIMATION: Hidden Progress Bar
        const progressInterval = setInterval(() => {
          setHiddenProgress((prev) => {
            if (prev >= 100) {
              clearInterval(progressInterval);
              return 100;
            }
            return prev + 5; // increment
          });
        }, 100);

        setTimeout(() => {
          clearInterval(progressInterval);
          setHiddenProgress(100);
          setTestStatus("passed_all");

          setTimeout(() => {
            if (taskIndex < INTERVIEW_TASKS.length - 1) {
              setTaskIndex((prev) => prev + 1);
              setTestStatus("idle");
              setCode(LANGUAGE_TEMPLATES[language]);
              setMessages((prev) => [
                ...prev,
                {
                  sender: "ai",
                  text: "Отлично! Переходим к следующей задаче.",
                },
              ]);
              setHiddenProgress(0);
            } else {
              setFinished(true);
            }
          }, 2000);
        }, 2500); // Time for hidden tests
      }, 1000);
    }, 1500);
  };

  const preventCopyPaste = (e) => {
    e.preventDefault();
    alert("Копирование и вставка запрещены правилами собеседования.");
  };

  if (disqualified) {
    return (
      <div className="h-screen bg-red-950 flex flex-col items-center justify-center text-center p-10 font-sans">
        <ShieldAlert size={80} className="text-red-500 mb-6" />
        <h1 className="text-4xl text-white font-bold mb-4">
          Собеседование прекращено
        </h1>
        <p className="text-xl text-red-200 mb-8 max-w-xl">
          Нарушение: <br />
          <span className="font-bold">{disqReason}</span>
        </p>
        <button
          onClick={onExit}
          className="bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded font-bold transition"
        >
          Вернуться на главную
        </button>
      </div>
    );
  }

  if (timeOut) {
    return (
      <div className="h-screen bg-slate-900 flex flex-col items-center justify-center text-center p-10 font-sans">
        <Clock size={80} className="text-orange-500 mb-6" />
        <h1 className="text-4xl text-white font-bold mb-4">Время вышло</h1>
        <p className="text-xl text-slate-300 mb-8 max-w-xl">
          К сожалению, вы не уложились в отведенное время (60 минут).
        </p>
        <button
          onClick={onExit}
          className="bg-orange-600 hover:bg-orange-500 text-white px-8 py-3 rounded font-bold transition"
        >
          Вернуться на главную
        </button>
      </div>
    );
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
        <div className="absolute inset-0 z-50 bg-red-900/90 flex flex-col items-center justify-center backdrop-blur-sm animation-pulse">
          <AlertTriangle size={100} className="text-white mb-4" />
          <h2 className="text-4xl font-bold text-white text-center">
            ВЕРНИТЕ КУРСОР!
          </h2>
          <p className="text-white text-xl mt-4 font-bold">
            Прерывание через {timerCount}...
          </p>
        </div>
      )}

      {finished && (
        <div className="absolute inset-0 z-50 bg-slate-900/95 flex flex-col items-center justify-center backdrop-blur-sm">
          <div className="bg-slate-800 p-10 rounded-2xl border border-green-500/30 text-center shadow-2xl max-w-lg">
            <div className="w-20 h-20 bg-green-900/50 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500">
              <CheckCircle2 className="text-green-400 w-10 h-10" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">
              Вы успешно сдали задачи!
            </h2>
            <p className="text-slate-300 mb-8">
              Все тесты (видимые и скрытые) пройдены.
            </p>
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
          <span className="font-bold text-white text-lg font-sans">
            VibeCode Jam
          </span>
          <span
            className={`bg-slate-800 text-xs px-2 py-1 rounded border ${
              timeLeft < 300
                ? "border-red-500 text-red-400 animate-pulse"
                : "border-slate-700 text-slate-400"
            } flex items-center gap-2`}
          >
            <Clock size={12} /> {formatTime(timeLeft)}
          </span>
          <span className="text-xs text-slate-500">
            Task {taskIndex + 1}/{INTERVIEW_TASKS.length}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRun}
            disabled={testStatus === "running"}
            className="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded text-sm text-white flex items-center gap-2 transition"
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
                  <h2 className="text-white text-xl m-0">
                    {currentTask.title}
                  </h2>
                  <span
                    className={`text-xs px-2 py-1 rounded uppercase font-bold ${
                      currentTask.difficulty === "Easy"
                        ? "bg-green-900 text-green-300"
                        : "bg-yellow-900 text-yellow-300"
                    }`}
                  >
                    {currentTask.difficulty}
                  </span>
                </div>
                <p>{currentTask.description}</p>
                <div className="bg-slate-950 p-3 rounded border border-slate-800 mt-4">
                  <pre className="text-sm font-mono whitespace-pre-wrap">
                    {currentTask.example}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex-1 space-y-4 mb-4 overflow-y-auto">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${
                        msg.sender === "me" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] p-3 rounded-lg text-sm ${
                          msg.sender === "me"
                            ? "bg-blue-600 text-white"
                            : "bg-slate-800 text-slate-200"
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
                        {
                          sender: "ai",
                          text: "Подсказка: Попробуйте использовать хеш-таблицу для поиска дополнения числа за O(1).",
                        },
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
                    />
                    <button
                      onClick={() =>
                        setMessages([
                          ...messages,
                          { sender: "me", text: inputMsg },
                        ])
                      }
                      className="p-2 bg-blue-600 rounded text-white"
                    >
                      <Send size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel with Resizable Output */}
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
              onChange={(value) => setCode(value)}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                automaticLayout: true,
              }}
            />
          </div>

          {/* DRAG HANDLE */}
          <div
            className="h-1 bg-slate-800 hover:bg-blue-500 cursor-row-resize flex items-center justify-center transition-colors"
            onMouseDown={() => setIsResizing(true)}
          >
            <GripHorizontal size={12} className="text-slate-600" />
          </div>

          {/* OUTPUT PANEL */}
          <div
            style={{ height: outputHeight }}
            className="bg-slate-900 flex flex-col transition-none"
          >
            <div className="h-8 bg-slate-800 px-4 flex items-center justify-between border-b border-slate-700 shrink-0">
              <span className="text-xs font-bold text-slate-400 uppercase">
                Test Results
              </span>
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

            <div className="flex-1 p-4 font-mono text-sm overflow-y-auto">
              {testStatus === "idle" && (
                <div className="space-y-3 opacity-50">
                  {currentTask.visibleTests.map((test, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950 p-3 rounded border border-slate-800"
                    >
                      <div className="text-xs text-slate-500 mb-1">
                        Case {idx + 1}
                      </div>
                      <div>Input: {test.input}</div>
                      <div>Expected: {test.expected}</div>
                    </div>
                  ))}
                </div>
              )}
              {(testStatus === "passed_visible" ||
                testStatus === "checking_hidden" ||
                testStatus === "passed_all") && (
                <div className="space-y-3">
                  <div className="text-green-400 font-bold mb-2 flex items-center gap-2">
                    <CheckCircle2 size={16} /> Visible Tests Passed
                  </div>
                  {currentTask.visibleTests.map((test, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950 p-3 rounded border border-green-900/50 flex justify-between items-center"
                    >
                      <div>
                        <div className="text-xs text-slate-500">
                          Case {idx + 1}
                        </div>
                        <div className="text-slate-300">
                          Input: {test.input}
                        </div>
                      </div>
                      <div className="text-green-500 font-bold text-xs bg-green-900/20 px-2 py-1 rounded">
                        Passed
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* HIDDEN TESTS ANIMATION */}
              {testStatus === "checking_hidden" && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-blue-400 text-xs font-bold flex items-center gap-2">
                      <Lock size={12} /> Running Hidden Tests...
                    </span>
                    <span className="text-blue-400 text-xs">
                      {hiddenProgress}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-100 ease-linear"
                      style={{ width: `${hiddenProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {testStatus === "passed_all" && (
                <div className="mt-4 pt-4 border-t border-slate-800 animate-in fade-in slide-in-from-bottom-2">
                  <div className="flex items-center gap-2 text-green-400 font-bold mb-2">
                    <Lock size={16} /> Hidden Tests
                  </div>
                  <div className="bg-green-900/20 border border-green-800 p-3 rounded text-green-300 text-center">
                    15/15 Hidden Test Cases Passed! 🎉
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [currentPage, setCurrentPage] = useState("login");
  const handleLogin = () => setCurrentPage("hr");
  const handleLogout = () => setCurrentPage("login");
  const handleStartInterview = () => setCurrentPage("interview");

  return (
    <>
      {currentPage === "login" && <LoginPage onLogin={handleLogin} />}
      {currentPage === "hr" && (
        <HRDashboard
          onNavigateToInterview={handleStartInterview}
          onLogout={handleLogout}
        />
      )}
      {currentPage === "interview" && <InterviewRoom onExit={handleLogout} />}
    </>
  );
}
