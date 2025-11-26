export const INTERVIEW_TASKS = [
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
    description: "Найдите длину самой длинной подстроки без повторяющихся символов.",
    example:
      'Input: s = "abcabcbb"\nOutput: 3\nExplanation: The answer is "abc", with the length of 3.',
    visibleTests: [
      { input: '"abcabcbb"', expected: "3" },
      { input: '"bbbbb"', expected: "1" },
    ],
  },
];
