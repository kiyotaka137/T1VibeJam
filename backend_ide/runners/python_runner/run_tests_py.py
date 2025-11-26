# runner/run_tests.py
import importlib
import json
import os
import sys


def main(job_dir: str):
    # В job_dir лежат:
    # - solution.py  (код кандидата)
    # - cases.json   (массив тестов [{input, output}, ...])

    os.chdir(job_dir)
    sys.path.insert(0, job_dir)

    # 1. Загружаем тест-кейсы
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
                "traceback": f"Can't read cases.json: {repr(e)}"
            }]
        }, ensure_ascii=False))
        return

    # 2. Импортируем решение
    try:
        solution = importlib.import_module("solution")
    except Exception as e:
        print(json.dumps({
            "testsRun": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
            "failure_details": [{
                "test": 0,
                "traceback": f"Can't import solution.py: {repr(e)}"
            }]
        }, ensure_ascii=False))
        return

    if not hasattr(solution, "solve"):
        print(json.dumps({
            "testsRun": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
            "failure_details": [{
                "test": 0,
                "traceback": "There is no function solve in module solution"
            }]
        }, ensure_ascii=False))
        return

    passed = 0
    failures = []

    for test_id, case in enumerate(cases, 1):
        raw_input = case.get("input")
        expected = case.get("output")

        # поддерживаем один аргумент и несколько
        if isinstance(raw_input, list):
            args = raw_input
        else:
            args = [raw_input]

        try:
            result = solution.solve(*args)
        except Exception as e:
            failures.append({
                "test": test_id,
                "traceback": f"Runtime error: {repr(e)}"
            })
            continue

        if result != expected:
            failures.append({
                "test": test_id,
                "traceback": f"Expected {expected!r}, got {result!r}"
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
        print("Usage: run_tests.py <job_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
