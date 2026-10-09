# AILBUploading — Independent Project

This repository is an isolated version of the question-upload application. It consists of a Vite/React frontend, a Flask coordinator, and one or more Flask/Selenium backends. It contains no deployment link or credentials from another project.

## Safety first

This deployment has iMocha write operations enabled in `Backend/config.py`, so uploads can save changes without a host environment variable. Never deploy it with unapproved credentials or an unintended question bank.

Known legacy service endpoints and legacy MongoDB identifiers are rejected during configuration validation.

## Architecture

1. The browser loads the React frontend.
2. The frontend reads `VITE_COORDINATOR_URL` and asks `/next-backend` for a backend.
3. The backend exposes its generated RSA public key and accepts encrypted credentials.
4. When writes are explicitly enabled in a non-development environment, Selenium performs the iMocha workflow.
5. A successful upload increments a counter in the separately configured MongoDB database.

## Prerequisites

- Node.js 18 or newer
- Python 3.10 or newer
- Chrome/Chromium compatible with Selenium
- A separate MongoDB database for this project
- A non-production iMocha test account and question bank

## Environment configuration

Copy `.env.example` to `.env` for backend/coordinator development and copy `frontend/.env.example` to `frontend/.env.local` for Vite. Both destination files are ignored by Git.

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development`, `staging`, or `production`. |
| `FRONTEND_URL` | Canonical URL of this project's frontend. |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins; defaults to `FRONTEND_URL`. |
| `BACKEND_URLS` | Comma-separated URLs for this project's backend instances. |
| `MONGO_URL` | Connection string for this project's separate MongoDB deployment. No production fallback exists. |
| `MONGO_DATABASE` | New-project database name. |
| `MONGO_COLLECTION` | Counter collection name. |
| `COUNTER_ID` | Counter document identifier. |
| `IMOCHA_BASE_URL` | iMocha base address. Use only with an approved test account/environment. |
| `RSA_PRIVATE_KEY_PATH` | Path to this project's uncommitted private key. |
| `PORT` | Runtime port supplied to each Python service, normally by the hosting platform. |
| `VITE_COORDINATOR_URL` | Browser-visible URL of this project's coordinator. Set in `frontend/.env.local` or the frontend host. |

## RSA key setup

Generate a unique RSA-2048 key pair for this project. Keep `Backend/private_key.pem` uncommitted and provide its path through `RSA_PRIVATE_KEY_PATH`. `Backend/public_key.pem` may be committed and is useful for verification; the backend derives the served public key from the configured private key so the pair cannot drift at runtime.

Example with OpenSSL:

```powershell
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out Backend/private_key.pem
openssl pkey -in Backend/private_key.pem -pubout -out Backend/public_key.pem
```

For deployment, store the private key in a secret file and set `RSA_PRIVATE_KEY_PATH` to the mounted path. Never put private-key content in Git or a public environment variable.

## Backend setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r Backend\requirements.txt
python Backend\app.py
```

The local backend defaults to port `5001` and uses `debug=False`.

## Coordinator setup

In another terminal, with the same root `.env` configuration:

```powershell
.venv\Scripts\Activate.ps1
python coordinator_service.py
```

The coordinator defaults to port `5000`. Local `BACKEND_URLS` can contain ports `5001` and `5002`; start only the instances you configure.

## Frontend setup

```powershell
Copy-Item frontend\.env.example frontend\.env.local
Set-Location frontend
npm ci
npm run dev
```

The frontend defaults to Vite's local port `5173`. It fails clearly if `VITE_COORDINATOR_URL` is missing or points to a blocked legacy service.

## MongoDB

Create a new database and a least-privilege user dedicated to this project. Set `MONGO_URL`, `MONGO_DATABASE`, `MONGO_COLLECTION`, and `COUNTER_ID`. A missing `MONGO_URL` raises an error when counter persistence is required; there is no embedded or production fallback.

## iMocha write mode

iMocha writes are enabled directly in `Backend/config.py`. Use an approved iMocha account and question bank, new RSA keys, and a separate MongoDB database before deploying this build.

## Independent deployment

Create new hosting services rather than attaching to existing services:

1. A static frontend rooted at `frontend`, built with `npm ci && npm run build`, publishing `frontend/dist`.
2. A coordinator web service using `gunicorn coordinator_service:app`.
3. One or more backend web services rooted at `Backend`, using `gunicorn app:app` and new-project secret files/environment variables.
4. Set `VITE_COORDINATOR_URL`, `FRONTEND_URL`, `ALLOWED_ORIGINS`, and `BACKEND_URLS` to the newly assigned service URLs.
5. Attach only the new MongoDB credentials and the new RSA private-key secret file.

Do not enable iMocha writes during the first deployment. Verify CORS, coordinator routing, public-key retrieval, and blocked-write behavior first.
