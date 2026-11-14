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

The health test checks the HTTP status and the important response fields. The suite also covers data auditing, preparation, split generation, ML helpers, AI silver-label export and the message-analysis API. The combined local run passed **93 tests in 4.95s** before the latest multilingual candidate-audit module was added. That module adds 12 tests which must be included in the next local run. The test client uses the pinned httpx2 dependency required by the current Starlette TestClient.

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

The blind queue is a targeted error sample, not a representative sample. Routine manual annotation is not required. Save the supplied AI suggestion sidecar as data/private/model_artifacts/validation_label_ai_suggestions_sidecar.csv, then run the AI silver-label exporter documented in data/label_review_protocol.md. The exporter does not read the separate source/model key and keeps official review fields pending. Keep all message-level files private and never commit them.


## 9. Local text-only message analysis endpoint

The backend now exposes a development endpoint that loads the local TF-IDF + Logistic Regression artifact:

    POST http://127.0.0.1:8000/v1/messages/analyze

The model file must already exist at data/private/model_artifacts/tfidf_logistic_regression.joblib. If it does not exist, run the fixed baseline training script from the repository root:

    python data\train_text_baseline.py

Start the backend from the backend folder:

    python -m uvicorn app.main:app --reload

Example PowerShell request:

    $body = @{ text = "Your bank account will be blocked. Share your OTP now." } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/messages/analyze" -Method Post -ContentType "application/json" -Body $body

The endpoint returns a candidate label, per-class model scores, a short safety message and explicit limitations. Model scores are uncalibrated outputs, not probabilities of fraud. Every response remains provisional and sets review_required to true. The detector analyses text only; it does not inspect sender history, URL destinations, app state, device location or bank records.

The endpoint returns 503 when the local model artifact is missing or incompatible, and 422 for blank or oversized input. It never downloads a model from the internet. Keep the joblib artifact local and load only the model created by your own trusted training run.

See data/ai_annotation_policy.md for the silver-label workflow and its safeguards.


## 10. Optional resumable AI annotation of the prepared dataset

The AI batch runner is documented in [data/ai_annotation_policy.md](../data/ai_annotation_policy.md). Configure SOUL_LLM_BASE_URL, SOUL_LLM_API_KEY and SOUL_LLM_MODEL in the local root .env, then run from the repository root:

    python data\ai_annotate_prepared_dataset.py --allow-external-processing

This sends the locally prepared message text to the configured external provider. Do not run it until you have checked the provider's data retention and processing terms. The runner sends record_id and text only, never source_label or baseline label; it stores only AI labels/rationales and a run manifest under Git-ignored data/private/ai_annotations/. It saves progress after each batch and resumes safely. Low-confidence outputs become needs_review. This is an AI silver-label dataset, not verified ground truth.


## 11. Language/script safety guard

Before calling the local model, the message detector checks for non-Latin script and a conservative list of Romanized-Hindi markers. Messages with those indicators return `candidate_label=needs_review`; the baseline is not called. This avoids presenting the existing model as Hindi/Hinglish capable before those languages have been validated.

The check is deliberately heuristic, not a complete language detector. Latin-script text without a detected marker can still be Hindi, Hinglish or another language. Run the aggregate-only coverage audit from the repository root:

    python data\audit_language_coverage.py

It reports counts only and never prints message text or IDs. See [data/model_baseline.md](../data/model_baseline.md) and [data/ai_annotation_policy.md](../data/ai_annotation_policy.md).


## 12. Optional multilingual candidate audit

The first 14-language candidate is synthetic and binary (scam vs ham). It is not merged with the historical three-class baseline. See [data/multilingual_data_strategy.md](../data/multilingual_data_strategy.md).

Install the optional data loader in the active virtual environment:

    python -m pip install datasets

Then run from the repository root:

    python data/audit_multilingual_candidate.py

The script writes its row-level synthetic candidate copy and aggregate report under Git-ignored data/private/multilingual_candidates/. It does not train a model, change the original split or print message text. Keep the row-level CSV local/private.


## 13. Prepare the multilingual candidate and group-safe split

After the first candidate audit succeeds, run from the repository root:

    python data\prepare_multilingual_candidate.py

This creates a masked local derivative, conflict quarantine and group-safe 80/10/10 train/validation/test CSVs under data/private/multilingual_candidates/prepared/. It groups on the final masked model text and will not allow that text to cross partitions. It uses the source's binary scam-vs-ham target; it does not map it to SOUL's existing three classes. It does not train a model or change the Mendeley baseline.


The multilingual split utility requires prepared rows with group_id and model_text_sha256, which are generated by prepare_rows(). The test fixtures now include these required fields. The minimum-group check also validates unique masked-text groups before attempting StratifiedGroupKFold.




Optional repeatable PowerShell demo (three synthetic cases: suspicious KYC, safety-warning hard negative, and Devanagari abstention): run from the repository root after starting the API:

```powershell
.\\backend\\demo_safe_message_assessment.ps1
```

## 12. Safe message assessment and official guidance

The existing \`POST /v1/messages/analyze\` endpoint now adds:
- category-level keyword indicators (credential request, urgency/threat, KYC/account update, URL present, UPI context, remote access, payment wording);
- an explicit notice that indicators are text-pattern matches, not proof and not model features;
- curated official guidance cards from RBI, NPCI, DoT/Chakshu and the National Cyber Crime Reporting Portal / I4C;
- a retrieval-method note.

Run the full backend tests after pulling:

\`\`\`powershell
python -m pytest -q
\`\`\`

Start the backend from this \`backend\` directory:

\`\`\`powershell
python -m uvicorn app.main:app --reload
\`\`\`

In Swagger at http://127.0.0.1:8000/docs, use \`POST /v1/messages/analyze\` with synthetic text such as:

\`\`\`json
{
  "text": "URGENT: Your bank KYC will expire today. Share your OTP immediately at https://example.invalid"
}
\`\`\`

The response contains the existing model suggestion plus \`risk_indicators\`, \`official_guidance\`, and limitations. The current API still loads the historical Mendeley model. The ScamShield three-class model is a separate research artifact and is not integrated into this API.

The guidance module is a curated keyword retriever, not full RAG: no embeddings, vector database or LLM synthesis. URL presence is detected but the URL is not opened or reputation-checked. All assessments remain provisional and require human review. Use synthetic demo text only.
