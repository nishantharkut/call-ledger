# CallLedger

Capital call reconciliation using Django REST Framework, PostgreSQL, and React.

## Local setup

Requires Python 3.13, Node.js 22.12 or later, and Docker Compose.

Create a virtual environment (`py -3.13 -m venv .venv` on Windows) and activate it.
Copy `.env.example` to `.env` and set a local secret key and database password.

```sh
pip install -r backend/requirements.txt
docker compose up -d --wait
python backend/manage.py migrate --settings=config.local
python backend/manage.py runserver --settings=config.local
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Django runs at `http://127.0.0.1:8000`; Vite runs at `http://localhost:5173`.
The local settings module configures PostgreSQL without changing Django's generated settings file.

## Demo data

```sh
python backend/manage.py seed_demo --settings=config.local
```

This creates Northwind Ventures, Bluebird Capital, and their seven capital call line items.
Running it again preserves existing records and funded amounts.

## Checks

```sh
python backend/manage.py check --settings=config.local
python backend/manage.py test --settings=config.local
```

From `frontend/`:

```sh
npm run lint
npm run build
```
