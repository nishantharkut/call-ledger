# CallLedger

A bank reconciliation workspace for capital call payments, built with Django REST
Framework, PostgreSQL, and React.

[Open CallLedger](https://call-ledger-six.vercel.app/)

## Run locally

Requires Python 3.13, Node.js 22.12 or later, and Docker Compose.
Create and activate a virtual environment, then copy `.env.example` to `.env`.
Set `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`. Keep Airtable variables blank
unless enabling the bonus integration.

From the repository root:

```sh
pip install -r backend/requirements.txt
docker compose up -d --wait
python backend/manage.py migrate --settings=config.local
python backend/manage.py seed_demo --settings=config.local
python backend/manage.py runserver --settings=config.local
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open [localhost:5173](http://localhost:5173), choose an organization, and upload a CSV.
Repeating `seed_demo` preserves existing records and funding.

## Checks

With PostgreSQL running, from the repository root:

```sh
python backend/manage.py test reconciliation --settings=config.local
```

From `frontend/`, run `npm run format:check`, `npm run lint`, and `npm run build`.

See [ASSESSMENT_NOTES.md](ASSESSMENT_NOTES.md) for fresh-clone setup, the model
and API, assumptions, and Airtable configuration.
