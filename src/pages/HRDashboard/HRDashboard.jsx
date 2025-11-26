import React, { useMemo, useState } from "react";
import {
  ArrowUpFromLine,
  Calendar,
  Code,
  Database,
  History,
  LogOut,
  PlusCircle,
  Send,
  Tag,
  Terminal,
  Trophy,
} from "lucide-react";

export function HRDashboard({ onNavigateToInterview, onLogout }) {
  const [activeTab, setActiveTab] = useState("create");
  const [generatedLink, setGeneratedLink] = useState("");
  
  // --- НОВОЕ ПОЛЕ: Имя кандидата ---
  const [candidateName, setCandidateName] = useState("");
  const [interviewDifficulty, setInterviewDifficulty] = useState("Junior");

  // HISTORY
  const [historyFilterStatus, setHistoryFilterStatus] = useState("all");
  const [historySort, setHistorySort] = useState("dateDesc");

  const historyData = [
    { id: 1, candidate: "Alexey I.", date: "2023-11-24", score: 85, status: "Completed" },
    { id: 2, candidate: "Maria S.", date: "2023-11-25", score: 92, status: "Hire" },
    { id: 3, candidate: "John D.", date: "2023-11-20", score: 45, status: "Rejected" },
    { id: 4, candidate: "Ivan P.", date: "2023-11-26", score: 78, status: "Review" },
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

  // BANK
  const [bankFilterDifficulty, setBankFilterDifficulty] = useState("All");
  const [bankFilterTag, setBankFilterTag] = useState("All");
  
  const [llmDifficulty, setLlmDifficulty] = useState("Junior");

  const [manualTask, setManualTask] = useState({
    condition: "",
    tests: "",
    difficulty: "Junior",
    tags: "",
  });

  const [tasksData, setTasksData] = useState([
    { id: 1, title: "Two Sum", difficulty: "Junior", tags: ["Array", "Hash Table"] },
    { id: 2, title: "LRU Cache", difficulty: "Senior", tags: ["Design", "Linked List"] },
    { id: 3, title: "Valid Parentheses", difficulty: "Junior", tags: ["Stack", "String"] },
    { id: 4, title: "Merge Intervals", difficulty: "Middle", tags: ["Array", "Sorting"] },
    { id: 5, title: "Network Delay Time", difficulty: "Middle", tags: ["Graph", "BFS"] },
  ]);

  const handleAddTask = () => {
    const newTags = manualTask.tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const newTask = {
      id: Date.now(),
      title: "Новая задача (Manual)",
      difficulty: manualTask.difficulty,
      tags: newTags.length ? newTags : ["General"],
    };
    setTasksData([newTask, ...tasksData]);
    setManualTask({ condition: "", tests: "", difficulty: "Junior", tags: "" });
  };

  const allTags = useMemo(() => {
    const tags = new Set();
    tasksData.forEach((task) => task.tags.forEach((t) => tags.add(t)));
    return ["All", ...Array.from(tags).sort()];
  }, [tasksData]);

  const filteredTasks = tasksData.filter((task) => {
    const matchDiff = bankFilterDifficulty === "All" || task.difficulty === bankFilterDifficulty;
    const matchTag = bankFilterTag === "All" || task.tags.includes(bankFilterTag);
    return matchDiff && matchTag;
  });

  const generateLink = () => {
    // Можно добавить валидацию имени, если нужно
    // if (!candidateName.trim()) { alert("Введите имя кандидата"); return; }
    
    const uniqueId = Math.random().toString(36).substring(7);
    // В реальном приложении имя кандидата уходило бы на бэкенд при создании ссылки
    setGeneratedLink(`https://vibecode.io/interview/${uniqueId}?diff=${interviewDifficulty}&name=${encodeURIComponent(candidateName)}`);
  };

  const getDifficultyColor = (diff) => {
    switch (diff) {
      case "Junior": return "bg-green-100 text-green-700";
      case "Middle": return "bg-yellow-100 text-yellow-700";
      case "Senior": return "bg-red-100 text-red-700";
      default: return "bg-gray-100 text-gray-700";
    }
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
        {/* TAB: CREATE */}
        {activeTab === "create" && (
          <div className="bg-white p-8 rounded-xl shadow-sm max-w-2xl border border-gray-100">
            <h2 className="text-2xl font-bold mb-6 text-slate-800">Новое собеседование</h2>

            <div className="space-y-6">
              {/* НОВОЕ ПОЛЕ: ФИО КАНДИДАТА */}
              <div>
                <label className="block text-sm font-medium text-slate-600 mb-2">
                  ФИО Кандидата
                </label>
                <input
                  type="text"
                  placeholder="Иванов Иван Иванович"
                  className="w-full p-3 border rounded-lg bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 transition"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-600 mb-2">
                  Сложность
                </label>
                <select
                  className="w-full p-3 border rounded-lg bg-gray-50 outline-none"
                  value={interviewDifficulty}
                  onChange={(e) => setInterviewDifficulty(e.target.value)}
                >
                  <option>Junior</option>
                  <option>Middle</option>
                  <option>Senior</option>
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
                  <div className="flex flex-col">
                    <span className="text-xs text-green-600 font-bold mb-1 uppercase">Ссылка готова</span>
                    <span className="text-green-800 font-mono text-sm">{generatedLink}</span>
                  </div>
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

        {/* TAB: BANK */}
        {activeTab === "bank" && (
          <div className="grid grid-cols-2 gap-6 h-[650px]">
            {/* LEFT COLUMN */}
            <div className="flex flex-col gap-6">
              {/* Add Manual Task */}
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-lg mb-4 text-slate-800 flex items-center gap-2">
                  <ArrowUpFromLine size={18} /> Добавить задачу
                </h3>

                <div className="space-y-3">
                  <textarea
                    className="w-full p-2 border rounded bg-gray-50 text-sm h-16 outline-none resize-none"
                    placeholder="Условие задачи..."
                    value={manualTask.condition}
                    onChange={(e) => setManualTask({ ...manualTask, condition: e.target.value })}
                  />
                  <textarea
                    className="w-full p-2 border rounded bg-gray-50 text-sm h-16 font-mono outline-none resize-none"
                    placeholder='JSON тесты: [{"input": "...", "output": "..."}]'
                    value={manualTask.tests}
                    onChange={(e) => setManualTask({ ...manualTask, tests: e.target.value })}
                  />
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="flex-1 p-2 border rounded bg-gray-50 text-sm"
                      placeholder="Теги (Array, DP...)"
                      value={manualTask.tags}
                      onChange={(e) => setManualTask({ ...manualTask, tags: e.target.value })}
                    />
                    <select
                      className="w-1/3 p-2 border rounded bg-gray-50 text-sm"
                      value={manualTask.difficulty}
                      onChange={(e) => setManualTask({ ...manualTask, difficulty: e.target.value })}
                    >
                      <option>Junior</option>
                      <option>Middle</option>
                      <option>Senior</option>
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

              {/* Task List */}
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
                      <option value="Junior">Junior</option>
                      <option value="Middle">Middle</option>
                      <option value="Senior">Senior</option>
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
                          className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold ${getDifficultyColor(task.difficulty)}`}
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
                    <div className="text-center text-slate-400 text-sm mt-4">Задачи не найдены</div>
                  )}
                </ul>
              </div>
            </div>

            {/* RIGHT COLUMN: LLM CHAT */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-slate-800">
                <Terminal size={18} /> Генератор (Scibox LLM)
              </h3>

              <div className="flex-1 bg-slate-900 rounded-lg p-4 mb-4 overflow-y-auto text-sm custom-scrollbar">
                <div className="mb-4">
                  <p className="text-blue-400 font-bold mb-1">Scibox AI:</p>
                  <p className="text-slate-300">Опишите тему и уровень, я сгенерирую задачу.</p>
                </div>
                <div className="mb-4 text-right">
                  <p className="text-green-400 font-bold mb-1">HR:</p>
                  <span className="bg-slate-800 px-3 py-2 rounded text-white inline-block">
                    Задача на жадные алгоритмы (Middle)
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <select 
                  className="w-1/4 p-2 border rounded bg-gray-50 text-sm outline-none cursor-pointer"
                  value={llmDifficulty}
                  onChange={(e) => setLlmDifficulty(e.target.value)}
                >
                  <option>Junior</option>
                  <option>Middle</option>
                  <option>Senior</option>
                </select>

                <input
                  type="text"
                  placeholder="Тема задачи..."
                  className="flex-1 p-2 border rounded bg-gray-50 outline-none"
                />
                <button className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB: HISTORY */}
        {activeTab === "history" && (
          <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-slate-800">История собеседований</h2>
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
                  <tr key={item.id} className="border-b last:border-0 hover:bg-gray-50 transition">
                    <td className="py-4 pl-2 font-medium text-slate-700">{item.candidate}</td>
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
}