# Treatment Plan Coordination Platform

> Open-source platform for treatment-plan progress coordination. Synthetic data only; **not for clinical use**.

[中文说明](README.md)

## What it is

Treatment Plan Coordination Platform coordinates a treatment plan across patients, caregivers, clinicians, hospitals, regulators and pharmaceutical companies. It is a modular monolith with one API contract shared by a Vue 3 web workspace, a Kotlin Compose patient app and a native WeChat mini-program (sandbox).

## Features

- Treatment templates, versioned plans, tasks, medications, observations and alerts.
- Caregiver authorization with field-level scopes and expiry; revocation takes effect immediately.
- Hospital-scoped access and cross-tenant isolation.
- Government aggregation with small-cell suppression; pharma signals only above 3 organizations / 50 patient-months.
- Versioned imports of public snapshots (NMPA / NHSA / NHC / NBS) with checksum and status rules.
- Reserved ports for HIS, medical insurance, government and supply-chain integrations; unconfigured ports fail explicitly.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Patient | `patient` | `Pa2026!care` |
| Caregiver | `caregiver` | `Ca2026!care` |
| Doctor | `doctor` | `Do2026!care` |
| Hospital admin | `hospital` | `Ho2026!care` |
| Regulator | `regulator` | `Re2026!care` |
| Pharma | `pharma` | `Ph2026!care` |
| System admin | `admin` | `Ad2026!care` |

Sandbox credentials only; replace them before any deployment.

## Quick start (Windows)

Requirements: Python 3.13 and Node.js 24 (with corepack).

```powershell
.\scripts\dev-up.cmd
```

The script creates the backend virtual environment, installs dependencies, seeds demo data and opens the API and web servers. Web: <http://localhost:5173>; API docs: <http://127.0.0.1:8000/docs>.

## Manual start

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m carepath.seed
.\.venv\Scripts\uvicorn carepath.main:app --reload --port 8000

cd ../apps/web
corepack enable
pnpm install
pnpm dev
```

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src tests migrations scripts

cd ../apps/web
pnpm test; pnpm lint; pnpm build
pnpm test:e2e   # install Playwright chromium first

cd ../apps/wechat
npm test; npm run check
```

CI runs 7 jobs: backend tests + lint, PostgreSQL smoke, web test/lint/build, web E2E, WeChat checks, Android build + JUnit, and security scans.

## Roadmap

See [ROADMAP.md](ROADMAP.md). Near-term: caregiver revocation UI, Docker Compose verification, WeChat AppID flow. Not planned: AI diagnosis, e-prescription, insurance settlement.

## Contributing and feedback

Issues, discussions and PRs are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); use [Discussions](https://github.com/zhouPi-314/carepath/discussions) for ideas and [Issues](https://github.com/zhouPi-314/carepath/issues) for bugs.

## License

Apache-2.0 OR MIT, at your option. See [LICENSE-APACHE](LICENSE-APACHE) and [LICENSE-MIT](LICENSE-MIT).
