import json
import os
import subprocess
import sys

def _flatten(value):
    """
    Рекурсивно расплющивает вложенные списки/кортежи.
    Примеры:
      [1, 2, 3]           -> [1, 2, 3]
      [[1, 2], 7]         -> [1, 2, 7]
      [[[1], [2, 3]], 4]  -> [1, 2, 3, 4]
    Строки НЕ трогаем (иначе разобьём на символы).
    """
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _flatten(item)
    else:
        yield value


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
    first_failed_index = None
    first_failed_id = None
    first_failed_type = None

    # 3. Гоним тесты
    for idx, case in enumerate(cases):

        cid = idx+1

        raw_stdin = case.get("input", None)

        if isinstance(raw_stdin, (list, tuple)):
            tokens = list(_flatten(raw_stdin))
            stdin = " ".join(str(x) for x in tokens)
        else:
            stdin = "" if raw_stdin is None else str(raw_stdin)

        expected_raw = case.get("output", None)

        expected_out = "" if expected_raw is None else str(expected_raw).strip()

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
                "traceback": f"Timeout: {repr(e)}",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "timeout"
            break  

        if proc.returncode != 0:
            failures.append({
                "test": cid,
                "traceback": f"Non-zero exit code {proc.returncode}, stderr={proc.stderr!r}",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "runtime_error"
            break  

        actual = (proc.stdout or "").strip()

        if actual != expected_out:
            failures.append({
                "test": cid,
                "traceback": f"Expected {expected_out!r}, got {actual!r}",
            })
            first_failed_index = idx
            first_failed_id = cid
            first_failed_type = "wrong_answer"
            break
        else:
            passed += 1

    out = {
        "testsRun": len(cases),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "passed": passed,
        "failure_details": failures,
        "first_failed_index": first_failed_index,
        "first_failed_id": first_failed_id,
        "first_failed_type": first_failed_type,
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_tests_cpp.py <job_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
