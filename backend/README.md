# SOUL Backend — Milestone 1

This folder contains the first small backend increment: a FastAPI app, environment-based settings, and a health endpoint.

> **Status:** Milestone 1's local verification is complete. The API was started successfully, the /health response was checked in a browser, and the automated test passed (1 passed, no warnings).

## Requirements

- Python 3.13 (verified locally with Python 3.13.0)
- Git
- PowerShell on Windows

## 1. Prepare local environment

Run these commands from the repository root (`SOUL` folder):

```powershell
Copy-Item .env.example .env
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The test client dependency is pinned as `httpx2` to match the current Starlette TestClient recommendation and avoid the deprecation warning seen with the older `httpx` client.

The virtual environment keeps SOUL packages separate from other Python projects on your computer. The `.env` file contains local settings and is ignored by Git.

If PowerShell blocks activation scripts, run this in the same terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Start the API

From the `backend` folder, with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --reload
```

Open these addresses in your browser:

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Expected health response (the service name/version can change through `.env`):

```json
{
  "status": "ok",
  "service": "SOUL API",
  "version": "0.1.0"
}
```

Stop the server with `Ctrl + C`.

## 3. Run automated tests

Still inside the `backend` folder:

```powershell
python -m pytest -q
```

The health test checks the HTTP status and the important response fields. The local verification recorded on 10 November 2026 completed successfully: 1 passed, no warnings. The test client uses the pinned httpx2 dependency required by the current Starlette TestClient.

## 4. Configuration

The repository-root `.env.example` shows the supported development settings:

- `SOUL_APP_NAME`: API name shown in documentation and the health response.
- `SOUL_APP_VERSION`: version shown in the health response.
- `SOUL_ENV`: `development` enables FastAPI debug mode; use a non-development value to disable it.

Never commit your real `.env` file, credentials, OTPs, bank data or API keys.
