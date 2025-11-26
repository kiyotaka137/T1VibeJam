// node-runner/run_tests.js
const fs = require("fs");
const path = require("path");

async function main() {
  const jobDir = process.argv[2] || "/backend_ide/job";
  const casesPath = path.join(jobDir, "cases.json");

  let cases;
  try {
    const raw = fs.readFileSync(casesPath, "utf8");
    cases = JSON.parse(raw);
  } catch (e) {
    console.log(JSON.stringify({
      testsRun: 0,
      failures: 0,
      errors: 1,
      skipped: 0,
      passed: 0,
      failure_details: [{
        test: 0,
        traceback: "Не удалось прочитать/распарсить cases.json: " + String(e),
      }],
    }));
    return;
  }

  let solution;
  try {
    solution = require(path.join(jobDir, "solution.js"));
  } catch (e) {
    console.log(JSON.stringify({
      testsRun: 0,
      failures: 0,
      errors: 1,
      skipped: 0,
      passed: 0,
      failure_details: [{
        test: 0,
        traceback: "Не удалось импортировать solution.js: " + String(e),
      }],
    }));
    return;
  }

  if (!solution || typeof solution.solve !== "function") {
    console.log(JSON.stringify({
      testsRun: 0,
      failures: 0,
      errors: 1,
      skipped: 0,
      passed: 0,
      failure_details: [{
        test: 0,
        traceback: "В модуле solution.js нет функции solve",
      }],
    }));
    return;
  }

  const failures = [];
  let passed = 0;

  for (let i = 0; i < cases.length; i++) {
    const c = cases[i];
    const id = i;
    const input = c.input;
    const expected = c.output;

    const args = Array.isArray(input) ? input : [input];

    try {
      let result = solution.solve(...args);

      // поддержка async solve
      if (result && typeof result.then === "function") {
        result = await result;
      }

      const actualNorm = JSON.stringify(result);
      const expectedNorm = JSON.stringify(expected);

      if (actualNorm !== expectedNorm) {
        failures.push({
          test: id,
          traceback: `Expected ${expectedNorm}, got ${actualNorm}`,
        });
      } else {
        passed++;
      }
    } catch (e) {
      failures.push({
        test: id,
        traceback: "Runtime error: " + String(e),
      });
    }
  }

  const out = {
    testsRun: cases.length,
    failures: failures.length,
    errors: 0,
    skipped: 0,
    passed,
    failure_details: failures,
  };

  // единственный console.log — итог раннера
  console.log(JSON.stringify(out));
}

main().catch((e) => {
  console.log(JSON.stringify({
    testsRun: 0,
    failures: 0,
    errors: 1,
    skipped: 0,
    passed: 0,
    failure_details: [{
      test: 0,
      traceback: "Fatal error in JS runner: " + String(e),
    }],
  }));
});
