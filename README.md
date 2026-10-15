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

## CSV import

`POST /api/imports/` accepts a multipart upload named `file` and requires
`X-Organization: northwind` or `X-Organization: bluebird`. The response contains
`imported`, `duplicates`, `duplicate_rows`, and `errors`. Row details include their
physical file line number; the header is line 1.

Files must use UTF-8 (an optional BOM is accepted) and be no larger than 10 MB.
Required columns are `date,description,amount,type,reference`; column order does
not matter. Extra named columns and blank lines are ignored. Duplicate or empty
column names reject the file. Each data row must have the same width as the header.

Amounts accept correctly grouped thousands separators and at most two decimal
places, within the model's 18-digit precision. Bank references are trimmed,
case-sensitive, and limited to 255 characters. Invalid rows report their first
validation error. Invalid encoding or headers reject the whole file without writes.

Debits are stored as ignored. Credits first match eligible wire references, then
investor names with an exact remaining amount. A single reference permits partial
payments; overpayments and ambiguous or unmatched credits need review. Suggestions
and reasons are stored once at import. Re-uploading does not recalculate them.
Importing does not change funded amounts.

## Reconciliation API

All endpoints require `X-Organization`. Missing or blank headers return `400`.
Unknown organizations and records outside the selected organization return `404`.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/transactions/?page=1` | Transactions ordered by date and ID descending, with matches and reasons. Pages contain up to 50 rows. |
| GET | `/api/line-items/` | All line items with investor, call details, amounts, and derived status. |
| POST | `/api/matches/{id}/approve/` | Approve a proposed match and update funding atomically. |
| POST | `/api/matches/{id}/reject/` | Reject a proposal. The last rejection leaves the payment needing review. |
| POST | `/api/transactions/{id}/ignore/` | Ignore an active credit and reject its matches. |

The transaction list returns `count`, `next`, `previous`, and `results`. The line-item
list is an unpaginated array. Money values are decimal strings. Successful actions
return `transaction_id` and `status`. Refresh both lists after an action.

Approval locks the transaction, then the line item, and checks the current remaining
amount before funding. A stale overpayment or repeated approval returns `409`
without changing funding. Actions on rejected proposals or on reconciled or ignored
transactions also return `409`. Only suggested or needs-review credits accept actions.

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
