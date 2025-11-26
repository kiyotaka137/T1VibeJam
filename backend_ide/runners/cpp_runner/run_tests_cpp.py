import json
import os
import subprocess
import sys


def main(job_dir: str):
    # В job_dir лежат:
    #  - solution.cpp  (код кандидата)
    #  - cases.json    (массив тестов [{id, stdin, stdout}, ...])

    os.chdir(job_dir)

    # 1. Читаем cases.json
    try:
        with open("cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
    except Exception as e:
        print(json.dumps({
            "testsRun": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
            "failure_details": [{
                "test": 0,
                "traceback": f"Не удалось прочитать/распарсить cases.json: {repr(e)}"
            }],
        }, ensure_ascii=False))
        return

    # 2. Компилируем solution.cpp -> main
    compile_proc = subprocess.run(
        ["g++", "-std=c++17", "-O2", "solution.cpp", "-o", "main"],
        capture_output=True,
        text=True,
    )

    if compile_proc.returncode != 0:
        print(json.dumps({
            "testsRun": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
            "failure_details": [{
                "test": 0,
                "traceback": f"Ошибка компиляции: {compile_proc.stderr}"
            }],
        }, ensure_ascii=False))
        return

    failures = []
    passed = 0

    # 3. Гоним тесты
    for idx, case in enumerate(cases):
        cid = idx+1
        data_to_input = case.get("input", "")
        stdin = " ".join(str(x) for x in data_to_input)
        expected_out = case.get("output")
        if expected_out is None:
            expected_out = ""
        else:
            expected_out = str(expected_out).strip()

        try:
            proc = subprocess.run(
                ["./main"],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except subprocess.TimeoutExpired as e:
            failures.append({
                "test": cid,
                "traceback": f"Timeout: {repr(e)}"
            })
            continue

        if proc.returncode != 0:
            failures.append({
                "test": cid,
                "traceback": f"Non-zero exit code {proc.returncode}, stderr={proc.stderr!r}"
            })
            continue

        actual = proc.stdout.strip()
        if actual != expected_out:
            failures.append({
                "test": cid,
                "traceback": f"Expected {expected_out!r}, got {actual!r}"
            })
        else:
            passed += 1

    tests_run = len(cases)
    out = {
        "testsRun": tests_run,
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "passed": passed,
        "failure_details": failures,
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_tests_cpp.py <job_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
