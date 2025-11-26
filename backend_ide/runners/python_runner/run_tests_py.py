# runner/run_tests.py
import importlib
import json
import os
import sys
import time

PER_CASE_SOFT_TIMEOUT = 2.0  # лимит на один тест, сек


def main(job_dir: str):
    # В job_dir лежат:
    # - solution.py  (код кандидата)
    # - cases.json   (массив тестов [{id, input, output|expected}, ...])

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
        module = importlib.import_module("solution")
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

    # Ожидаем, что в solution.py есть функция main(...)
    if not hasattr(module, "main"):
        print(json.dumps({
            "testsRun": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
            "failure_details": [{
                "test": 0,
                "traceback": "There is no function main in module solution"
            }]
        }, ensure_ascii=False))
        return

    solve = getattr(module, "main")

    passed = 0
    failures = []
    first_failed_index = None
    first_failed_id = None
    first_failed_type = None  # "wrong_answer" / "runtime_error" / "timeout"

    # 3. Гоним тесты
    for idx, case in enumerate(cases):
        cid = case.get("id", f"case_{idx + 1}")
        input_data = case["input"]
        expected = case.get("expected", case.get("output"))

        # input может быть либо списком аргументов, либо одним значением
        args = input_data if isinstance(input_data, list) else [input_data]

        start = time.perf_counter()
        try:
            result = solve(*args)
        except Exception as e:
            failures.append({
                "test": cid,
                "traceback": f"Runtime error: {repr(e)}",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "runtime_error"
            break

        elapsed = time.perf_counter() - start
        if elapsed > PER_CASE_SOFT_TIMEOUT:
            failures.append({
                "test": cid,
                "traceback": f"Timeout: {elapsed:.3f} seconds",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "timeout"
            break

        # сравнение результата (можно улучшить под сложные типы, но пока так)
        if result != expected:
            failures.append({
                "test": cid,
                "traceback": f"Wrong answer: expected {expected!r}, got {result!r}",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "wrong_answer"
            break
        else:
            passed += 1

    # 4. Печатаем ОДИН раз итоговый JSON (а не в цикле!)
    out = {
        "testsRun": len(cases),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "passed": passed,
        "failure_details": failures,
        "first_failed_index": first_failed_index,  # 0-based
        "first_failed_id": first_failed_id,
        "first_failed_type": first_failed_type,
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_tests.py <job_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
