FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Shell form so ${PORT} expands: Render (and most PaaS) inject $PORT and route
# their health check to it. Exec form (JSON array) does NOT expand env vars,
# so a hardcoded --port 8000 leaves the service unreachable behind $PORT.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
