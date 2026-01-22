FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
COPY ./app .
CMD sh -c "echo '=== Running linters ===' && black --check . && echo '✅ Black: OK' || echo '⚠ Black: Needs formatting' && echo '=== Running security checks ===' && bandit -r . -l && echo '✅ Bandit: Security check completed' && safety check && echo '✅ Safety: Dependencies check completed' && echo '=== Running tests ===' && python -m pytest test_main.py -v || echo '⚠ Pytest failed' && echo '=== Starting FastAPI application ===' && uvicorn main:app --host 0.0.0.0 --port 8000"