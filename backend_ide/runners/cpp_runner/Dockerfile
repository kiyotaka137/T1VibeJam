FROM python:3.11-slim

RUN apt-get update && apt-get install -y g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /backend_ide

COPY run_tests_cpp.py /backend_ide/run_tests_cpp.py

ENTRYPOINT ["python", "/backend_ide/run_tests_cpp.py"]
