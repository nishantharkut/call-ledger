import json
from http.client import HTTPException
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings


class AirtableError(Exception):
    pass


class AirtableClient:
    def __init__(self, token, base_id, table_name):
        if not all((token, base_id, table_name)):
            raise AirtableError("Airtable configuration is incomplete.")

        self.token = token
        self.url = (
            f"https://api.airtable.com/v0/{quote(base_id, safe='')}/"
            f"{quote(table_name, safe='')}"
        )
        self.next_request_at = 0

    @classmethod
    def from_settings(cls):
        config = (
            settings.AIRTABLE_PAT,
            settings.AIRTABLE_BASE_ID,
            settings.AIRTABLE_TABLE_NAME,
        )
        if not any(config):
            return None

        return cls(*config)

    def create_records(self, fields):
        if not 1 <= len(fields) <= 10:
            raise AirtableError("Create requests require between one and ten records.")

        # Pace batches within this upload below Airtable's five requests per second.
        delay = self.next_request_at - monotonic()
        if delay > 0:
            sleep(delay)
        self.next_request_at = monotonic() + 0.25

        body = json.dumps({"records": [{"fields": row} for row in fields]})
        request = Request(
            self.url,
            data=body.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=5) as response:
                result = json.load(response)
        except HTTPError as error:
            # Do not include upstream bodies or authorization values in error messages.
            raise AirtableError(f"Airtable returned HTTP {error.code}.") from None
        except (URLError, OSError, HTTPException):
            raise AirtableError("Airtable could not be reached.") from None
        except (ValueError, UnicodeError):
            raise AirtableError("Airtable returned an unreadable response.") from None

        if not isinstance(result, dict) or not isinstance(result.get("records"), list):
            raise AirtableError("Airtable returned an unexpected response.")

        return result["records"]
