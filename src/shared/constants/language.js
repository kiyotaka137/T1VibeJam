export const LANGUAGE_TEMPLATES = {
  javascript: `// Напишите решение здесь\nfunction solve(input) {\n  return input;\n}`,
  python: `# Write your solution here\ndef solve(input_data):\n    return input_data`,
  cpp: `// Write your solution here\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> solve(vector<int>& nums) {\n        return nums;\n    }\n};`,
  java: `// Write your solution here\nclass Solution {\n    public int[] solve(int[] nums) {\n        return nums;\n    }\n}`,
  go: `// Write your solution here\npackage main\n\nfunc solve(input []int) []int {\n    return input\n}`,
};

export const DISPLAY_LANGUAGES = {
  javascript: "JavaScript",
  python: "Python",
  cpp: "C++",
  java: "Java",
  go: "Go",
};

export const EDITOR_LANGUAGES = Object.keys(LANGUAGE_TEMPLATES);
