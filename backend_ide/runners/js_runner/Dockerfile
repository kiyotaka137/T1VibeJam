# node-runner/Dockerfile
FROM node:20-alpine

WORKDIR /backend_ide

COPY run_tests_js.js /backend_ide/runners/js_runner/run_tests_js.js

ENTRYPOINT ["node", "/backend_ide/runners/js_runner/run_tests_js.js"]