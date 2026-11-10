# SOUL Backend — Milestone 1

This folder contains the first small backend increment: a FastAPI app, environment-based settings, and a health endpoint.

> **Status:** Starter code has been added to GitHub. It still needs to be run and tested on a local computer before Milestone 1 can be marked complete.

## Requirements

- Python 3.13 (the project development environment currently targets Python 3.13)
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

The health test checks the HTTP status and the important response fields. A passing local test run is required before Milestone 1 is complete.

## 4. Configuration

The repository-root `.env.example` shows the supported development settings:

- `SOUL_APP_NAME`: API name shown in documentation and the health response.
- `SOUL_APP_VERSION`: version shown in the health response.
- `SOUL_ENV`: `development` enables FastAPI debug mode; use a non-development value to disable it.

Never commit your real `.env` file, credentials, OTPs, bank data or API keys.
