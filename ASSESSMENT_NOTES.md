# Assessment Notes

App name: **CallLedger**.

## Setup from a fresh clone

Requires Python 3.13, Node.js 22.12 or later, and Docker Compose with Docker running.

```sh
git clone https://github.com/nishantharkut/call-ledger.git
cd call-ledger
python3.13 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

On Windows, replace the last three commands with `py -3.13 -m venv .venv`,
`.\.venv\Scripts\Activate.ps1`, and `Copy-Item .env.example .env`.

Set **DJANGO_SECRET_KEY** and **POSTGRES_PASSWORD** in the root **.env** file.
[.env.example](.env.example) contains the configuration variables without credentials.
Leave Airtable variables blank to run without the bonus.

```sh
pip install -r backend/requirements.txt
docker compose up -d --wait
python backend/manage.py migrate --settings=config.local
python backend/manage.py seed_demo --settings=config.local
python backend/manage.py runserver --settings=config.local
```

In a second terminal, from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open [localhost:5173](http://localhost:5173). Vite forwards API requests to Django on port 8000.
The seed command can be repeated without resetting funding.

## Tests

With the virtual environment active and PostgreSQL running, from the repository root:

```sh
python backend/manage.py test reconciliation --settings=config.local
```

## Data model

Organizations own investors, capital calls, and bank transactions. Line items connect
investors to calls and store their expected reference, called amount, and funded amount.
Remaining amounts and funding statuses are derived. Matches connect transactions to
line items and store a reason and status. Money uses decimal columns, and bank
references are unique per organization.

## API

Every endpoint requires the **X-Organization** header, for example `X-Organization: northwind`.
Missing headers return 400. Unknown organizations and foreign records return 404.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/imports/` | Multipart **file**. Returns imported count, duplicate count and row details, and row errors. |
| GET | `/api/transactions/?page=1` | Newest first, with matches and reasons. Defaults to 50 per page. |
| GET | `/api/line-items/` | All line items with called, funded, remaining, and status. |
| POST | `/api/matches/{id}/approve/` | Approve a proposal and update funding atomically. |
| POST | `/api/matches/{id}/reject/` | Reject a proposal. |
| POST | `/api/transactions/{id}/ignore/` | Ignore an active credit and reject its matches. |

Transaction lists return **count**, **next**, **previous**, and **results**. Line items are
an unpaginated array. Actions return **transaction_id** and **status**. Repeated or stale
approvals return 409. Money is returned as decimal strings.

Transactions also accept **search** for case-insensitive description and bank reference
search, **status** for an exact transaction status, and **ordering** (**-date**, **date**,
**-amount**, or **amount**). Filters apply before pagination. Newest first is the default.
The **page_size** parameter sets rows per page, capped at 500. The UI offers 50, 100, and 500.

## Airtable configuration

Set **AIRTABLE_PAT**, **AIRTABLE_BASE_ID**, and **AIRTABLE_TABLE_NAME** in the root **.env**,
then restart Django. The token needs **data.records:write** access to the base.
Use these exact field names:

| Type | Fields |
| --- | --- |
| Single line text | **Bank reference** (primary), **Transaction ID**, **Organization**, **Amount (USD)**, **Status** |
| Date without time | **Date** |
| Long text | **Description**, **Review reason** |

Newly imported **needs_review** transactions are created in Airtable after the database
commits. Record IDs and sync statuses are saved locally. Failures mark affected rows
**sync_failed** without undoing the import. Disabled integration leaves rows **not_synced**.

## Assumptions, trade-offs, and next steps

- Amounts display as USD because the CSV has no currency column. No conversion is applied.
- Uploads accept UTF-8 with an optional BOM, up to 10 MB. Amounts allow at most two decimal places. Extra named columns and blank lines are ignored.
- Bank references are trimmed and case-sensitive for duplicates. Row locations use physical starting lines.
- Suggestions are calculated once. Approval locks the payment and line item before checking the current balance. Same-organization imports are serialized for exact duplicate reporting.
- Airtable creates records only. Duplicates are not resent, and later review actions do not update records. Sync adds network time to uploads. Pacing is per upload, so concurrent uploads may hit the shared rate limit. Failed creates are not retried automatically because a timeout may follow a successful create.
- Next step: add manual recovery for failed Airtable syncs. Check for the Transaction ID in Airtable before retrying to avoid duplicate records.

## Deployment

- Frontend: https://call-ledger-six.vercel.app/
- API: https://call-ledger-api.onrender.com

React is hosted on Vercel. Django and PostgreSQL run on Render.

## Disclosure 

I completed this assessment without using AI assistance.