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

The health test checks the HTTP status and the important response fields. The broader suite also covers data auditing, preparation, split generation and ML baseline helpers. The latest full local run after source-label provenance changes passed: 45 passed in 5.25s. A new blinded validation-review queue and its 12 tests have since been added; run the suite again after pulling. The test client uses the pinned httpx2 dependency required by the current Starlette TestClient.

## 4. Configuration

The repository-root `.env.example` shows the supported development settings:

- `SOUL_APP_NAME`: API name shown in documentation and the health response.
- `SOUL_APP_VERSION`: version shown in the health response.
- `SOUL_ENV`: `development` enables FastAPI debug mode; use a non-development value to disable it.

Never commit your real `.env` file, credentials, OTPs, bank data or API keys.


## 5. Machine-learning baseline dependencies

The same virtual environment is used for the local dataset and ML scripts. The direct requirements now include pinned versions of scikit-learn and joblib for the first TF-IDF + Logistic Regression baseline. From the repository root, after pulling updated requirements, run:

```powershell
python -m pip install -r backend\requirements.txt
```

The training script is run from the repository root, not from the backend folder:

```powershell
python data\train_text_baseline.py
```

It reads the local split files under `data/private/mendeley_splits/`, trains on the train partition, reports validation metrics and a first fixed-recipe test evaluation, then stores the local model and aggregate metrics under `data/private/model_artifacts/`. The test set must not be used for tuning. See [data/model_baseline.md](../data/model_baseline.md).

Do not commit split files, metrics containing message content (none should be present), or model artefacts. Joblib files use pickle-based serialization; do not load an artifact from an untrusted source.


## 6. Validation-only baseline error analysis

After the first model run, execute this from the repository root:

```powershell
python data\\analyze_baseline_errors.py
```

This reads only the original validation split and verifies its SHA-256 against the saved baseline metadata. It does not retrain the model or read the initial test partition. Aggregate and message-level reports are saved locally under Git-ignored `data/private/model_artifacts/`. The message-level CSV contains text: inspect it locally and share aggregate counts only. Do not commit or upload it.


## 7. Source-label provenance update

The local Mendeley preparation script now preserves the original publisher category in `source_label`. The existing `label` field remains the provisional mapping used by the original frozen baseline. New `soul_label`, `review_status` and `annotation_note` fields are blank/pending until an independent human review. See [data/label_review_protocol.md](../data/label_review_protocol.md).

After pulling this update, run from the repository root:

```powershell
python data\\prepare_mendeley_dataset.py
python data\\validate_prepared_dataset.py
```

Do not rerun `data/create_mendeley_splits.py` or `data/train_text_baseline.py` as part of this step; preserve the existing baseline split and model. Then run the full pytest suite from `backend/`.


## 8. Blinded validation label-review queue

After the baseline error-analysis report exists and the regenerated prepared CSV has passed validation, run from the repository root:

```powershell
python data\build_validation_label_review_queue.py
```

This generates two local files under `data/private/model_artifacts/`:
- `validation_label_review_blind.csv`: text and blank SOUL review fields; no source label or prediction.
- `validation_label_review_key.csv`: original source label, provisional label, prediction and score; no message text.

Review the blind CSV first. Do not open the key until labels have been entered independently. This is a targeted error sample, not a representative sample. Keep both files private and do not commit or upload them. See [data/label_review_protocol.md](../data/label_review_protocol.md).
