"""
XSIAM Event Collector Scaffolder

Generates a ready-to-upload content pack for a "send events to dataset" integration.
These integrations pull events from a third-party API on a schedule and write them
into an XSIAM dataset via send_events_to_xsiam(), without creating incidents/alerts.
Alerting is left to correlation rules over the dataset.

CRITICAL: The generated pack MUST be installed as system content via sdk_upload with
--xsiam --zip flags. Loose custom upload fails with getLicenseCustomField error because
send_events_to_xsiam() calls getLicenseCustomField internally, which is only available
to system content. See Issue #22 for the working recipe.

Reference: Armis EventCollector (marketplace) and CheckPointHECsys (IMC tenant v4.1.0).
"""

import logging
import textwrap
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)


def _integration_yaml(vendor: str, product: str, api_description: str, fields: list[str]) -> str:
    """Generate the integration YAML for an event collector."""
    name = f"{vendor.title()}{product.title()}EventCollector"
    display = f"{vendor.title()} {product.title()} Event Collector"
    dataset = f"{vendor.lower()}_{product.lower()}_raw"

    fields_doc = "\n".join(f"    - {f}" for f in fields) if fields else "    - id\n    - timestamp\n    - event_type"

    return f"""commonfields:
  id: {name}
  version: -1
name: {name}
display: {display}
category: Analytics & SIEM
description: >-
  {api_description}
  Fetches events and writes them to the {dataset} dataset via send_events_to_xsiam.
  Install as system content (sdk_upload --xsiam --zip) — required for send_events_to_xsiam.
fromversion: 6.10.0
marketplaces:
  - marketplacev2
  - platform
supportedModules:
  - xsiam
configuration:
  - display: API Base URL
    name: base_url
    type: 0
    required: true
  - display: API Key
    name: api_key
    type: 9
    required: true
  - display: Maximum events per fetch
    name: max_events
    defaultvalue: "1000"
    type: 0
    required: false
  - display: Event Fetch Interval
    name: eventFetchInterval
    defaultvalue: "1"
    type: 19
    required: false
  - display: Trust any certificate (not secure)
    name: insecure
    type: 8
    required: false
  - display: Use system proxy settings
    name: proxy
    type: 8
    required: false
script:
  script: ""
  type: python
  subtype: python3
  dockerimage: demisto/python3:3.12.8.3296088
  isfetchevents: true
  commands:
    - name: {vendor.lower()}-{product.lower()}-get-events
      description: Manually fetch events for testing (does not advance the cursor).
      arguments:
        - name: limit
          description: Maximum number of events to return.
          defaultValue: "10"
      outputs:
        - contextPath: {vendor.title()}{product.title()}.Events
          description: List of fetched events.
          type: Unknown
"""


def _integration_python(vendor: str, product: str, fields: list[str]) -> str:
    """Generate the integration Python file skeleton."""
    name = f"{vendor.title()} {product.title()} Event Collector"
    fields_list = repr(fields) if fields else "['id', 'timestamp', 'event_type']"

    return textwrap.dedent(f'''\
        """
        {name}

        Fetches events from the {vendor.title()} {product.title()} API and writes them
        to the {vendor.lower()}_{product.lower()}_raw dataset via send_events_to_xsiam.

        INSTALL REQUIREMENT: Must be uploaded as system content via:
            demisto-sdk upload -i Packs/{vendor.title()}{product.title()}Collector --xsiam --zip
        Loose custom upload will fail with getLicenseCustomField error.

        Reference: Armis EventCollector pattern (marketplace).
        """
        import demistomock as demisto
        from CommonServerPython import *
        from datetime import datetime, timezone

        VENDOR = "{vendor.lower()}"
        PRODUCT = "{product.lower()}"
        DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        FIELDS = {fields_list}


        class Client(BaseClient):
            """API client for {vendor.title()} {product.title()}."""

            def get_events(self, from_time: str, to_time: str, limit: int = 1000) -> list[dict]:
                """Fetch events between from_time and to_time.

                TODO: Replace with actual API call.
                Returns list of event dicts, each with a timestamp field.
                """
                # Example skeleton — replace with real API call:
                # response = self._http_request(
                #     method="GET",
                #     url_suffix="/events",
                #     params={{"from": from_time, "to": to_time, "limit": limit}},
                # )
                # return response.get("events", [])
                raise NotImplementedError("Implement get_events() with actual API call")


        def add_time_to_events(events: list[dict]) -> None:
            """Set _time field from the event timestamp. Required by send_events_to_xsiam."""
            for event in events:
                # TODO: adjust the key name to match your API response
                ts = event.get("timestamp") or event.get("created_at") or event.get("time")
                if ts:
                    event["_time"] = ts


        def fetch_events(client: Client, last_run: dict, max_events: int) -> tuple[dict, list[dict]]:
            """Fetch events since last run, advance cursor. Returns (new_last_run, events)."""
            last_fetch = last_run.get("events_last_fetch")
            now = datetime.now(tz=timezone.utc)
            from_time = last_fetch or now.strftime(DATE_FORMAT)
            to_time = (now - timedelta(minutes=15)).strftime(DATE_FORMAT)  # 15-min lag for API consistency

            events = client.get_events(from_time=from_time, to_time=to_time, limit=max_events * 2)

            # Sort by timestamp before applying cap — ensures cursor advances to a true boundary
            events.sort(key=lambda e: e.get("timestamp") or e.get("created_at") or "")

            # Dedup guard: drop events at or before last fetch boundary
            if last_fetch:
                events = [e for e in events if (e.get("timestamp") or "") > last_fetch]

            # Apply cap after sorting and dedup
            events = events[:max_events]

            add_time_to_events(events)

            # Advance cursor to latest event time (not to 'now', to avoid gaps)
            if events:
                latest = max(e.get("timestamp") or "" for e in events)
                new_last_run = {{"events_last_fetch": latest}}
            else:
                new_last_run = last_run

            return new_last_run, events


        def main() -> None:
            params = demisto.params()
            args = demisto.args()
            command = demisto.command()

            client = Client(
                base_url=params["base_url"],
                verify=not params.get("insecure", False),
                proxy=params.get("proxy", False),
                headers={{"Authorization": f"Bearer {{params[\'api_key\']}}", "Content-Type": "application/json"}},
            )

            demisto.info(f"Command: {{command}}")

            try:
                if command == "test-module":
                    # Quick connectivity check — replace with a lightweight API call
                    return_results("ok")

                elif command == "fetch-events":
                    last_run = demisto.getLastRun()
                    max_events = int(params.get("max_events") or 1000)
                    new_last_run, events = fetch_events(client, last_run, max_events)
                    demisto.info(f"Fetched {{len(events)}} events from {vendor.title()} {product.title()}")
                    send_events_to_xsiam(events, vendor=VENDOR, product=PRODUCT)
                    demisto.setLastRun(new_last_run)

                elif command == "{vendor.lower()}-{product.lower()}-get-events":
                    limit = int(args.get("limit", 10))
                    last_run = demisto.getLastRun()
                    _, events = fetch_events(client, last_run, max_events=limit)
                    return_results(CommandResults(
                        outputs_prefix=f"{vendor.title()}{product.title()}.Events",
                        outputs=events,
                        readable_output=tableToMarkdown(
                            f"{vendor.title()} {product.title()} Events",
                            events,
                            headers=FIELDS,
                            removeNull=True,
                        ),
                    ))

                else:
                    raise NotImplementedError(f"Command {{command}} is not implemented")

            except Exception as e:
                demisto.error(f"{vendor.title()} {product.title()} Event Collector error: {{e}}")
                return_error(str(e))


        if __name__ in ("__main__", "__builtin__", "builtins"):
            main()
        ''')


def _pack_metadata(vendor: str, product: str) -> str:
    name = f"{vendor.title()}{product.title()}Collector"
    display = f"{vendor.title()} {product.title()} Event Collector"
    return f'''{{
  "name": "{display}",
  "description": "Fetches {vendor.title()} {product.title()} events into XSIAM dataset for detection.",
  "support": "community",
  "currentVersion": "1.0.0",
  "author": "Cortex Bot",
  "url": "",
  "email": "",
  "categories": ["Analytics & SIEM"],
  "tags": ["eventcollector", "xsiam", "{vendor.lower()}", "{product.lower()}"],
  "useCases": [],
  "keywords": [],
  "marketplaces": ["marketplacev2", "platform"]
}}
'''


def _readme(vendor: str, product: str) -> str:
    display = f"{vendor.title()} {product.title()} Event Collector"
    dataset = f"{vendor.lower()}_{product.lower()}_raw"
    return f"""# {display}

Fetches events from {vendor.title()} {product.title()} and writes them to the `{dataset}` XSIAM dataset.

## Installation — REQUIRED

This pack **must** be installed as system content:

```bash
uvx demisto-sdk upload -i Packs/{vendor.title()}{product.title()}Collector --xsiam --zip --insecure
```

> **Do not** use loose custom upload — `send_events_to_xsiam()` calls `getLicenseCustomField`
> which is only available to system content. Loose upload will fail silently or with a
> `getLicenseCustomField` error.

## Configuration

| Parameter | Description |
|-----------|-------------|
| API Base URL | Base URL of the {vendor.title()} {product.title()} API |
| API Key | Authentication key |
| Maximum events per fetch | Cap per scheduled run (default: 1000) |
| Event Fetch Interval | Minutes between fetches (default: 1) |

## Dataset

Events land in: `{dataset}`

Query with: `dataset = {dataset} | dedup id | limit 100`

## Detection

Create correlation rules over `{dataset}` for alerting. The integration does not create issues.
"""


async def scaffold_event_collector(
    ctx: Context,
    vendor: Annotated[str, Field(description="Vendor name (e.g. 'checkpoint', 'crowdstrike'). Used in dataset name: vendor_product_raw")],
    product: Annotated[str, Field(description="Product name (e.g. 'harmony', 'falcon'). Used in dataset name: vendor_product_raw")],
    api_description: Annotated[str, Field(description="One-sentence description of what API this collects from")],
    fields: Annotated[list, Field(description="List of key field names in the event payload (e.g. ['id', 'timestamp', 'src_ip', 'action'])")] = [],
) -> str:
    """
    Scaffold a ready-to-upload XSIAM event collector integration pack.

    Generates all files needed to build and upload an integration that pulls events
    from a third-party API on a schedule and writes them to an XSIAM dataset using
    send_events_to_xsiam() — WITHOUT creating incidents/alerts. Detection is done
    via correlation rules over the dataset.

    CRITICAL INSTALLATION REQUIREMENT:
    The generated pack MUST be installed as system content via sdk_upload with
    --xsiam --zip flags. Loose custom upload will fail with:
        'command getLicenseCustomField is only available for system content'
    This is because send_events_to_xsiam() internally calls getLicenseCustomField.

    Working recipe (proven — dataset grows on schedule, unattended):
    1. Generate pack with this tool
    2. Write your get_events() API call in the Python skeleton
    3. Upload: uvx demisto-sdk upload -i Packs/<PackName> --xsiam --zip --insecure
    4. Configure the integration in XSIAM Settings > Integrations

    The generated pack includes:
    - Integration YAML: isfetchevents=true, eventFetchInterval (type 19),
      marketplaces=[marketplacev2, platform], supportedModules=[xsiam], fromversion=6.10.0
    - Python skeleton: getLastRun/setLastRun cursor, sort-before-cap dedup,
      add_time_to_events(), send_events_to_xsiam(). No demisto.incidents().
    - Pack files: README.md, .pack-ignore, .secrets-ignore, pack_metadata.json

    Returns a dict of {filename: content} ready to write to disk and upload.

    Reference: Armis EventCollector (marketplace), CheckPointHECsys on IMC tenant v4.1.0.
    Issue: https://github.com/alexpekarovsky/cortex-bot/issues/22

    Args:
        vendor: Vendor name, lowercase (e.g. 'checkpoint'). Forms dataset: vendor_product_raw
        product: Product name, lowercase (e.g. 'harmony'). Forms dataset: vendor_product_raw
        api_description: Short description of the data source
        fields: Key field names present in the event payload for documentation

    Returns:
        Dict mapping filename → file content for all pack files
    """
    vendor = vendor.lower().strip()
    product = product.lower().strip()
    pack_name = f"{vendor.title()}{product.title()}Collector"
    int_name = f"{vendor.title()}{product.title()}EventCollector"

    pack_files = {
        f"Packs/{pack_name}/pack_metadata.json": _pack_metadata(vendor, product),
        f"Packs/{pack_name}/README.md": _readme(vendor, product),
        f"Packs/{pack_name}/.pack-ignore": "",
        f"Packs/{pack_name}/.secrets-ignore": "",
        f"Packs/{pack_name}/Integrations/{int_name}/{int_name}.yml": _integration_yaml(vendor, product, api_description, fields),
        f"Packs/{pack_name}/Integrations/{int_name}/{int_name}.py": _integration_python(vendor, product, fields),
    }

    upload_cmd = f"uvx demisto-sdk upload -i Packs/{pack_name} --xsiam --zip --insecure"
    dataset = f"{vendor}_{product}_raw"

    logger.info(f"Scaffolded event collector pack: {pack_name} ({len(pack_files)} files)")

    return create_response(data={
        "pack_name": pack_name,
        "dataset": dataset,
        "upload_command": upload_cmd,
        "warning": "MUST install as system content via sdk_upload --xsiam --zip. Loose upload fails.",
        "files": pack_files,
        "next_steps": [
            f"1. Write the get_events() method in Packs/{pack_name}/Integrations/{int_name}/{int_name}.py",
            f"2. Run: {upload_cmd}",
            "3. Configure integration in XSIAM: Settings > Integrations",
            f"4. Verify data lands in: dataset = {dataset} | limit 10",
            f"5. Create correlation rules over {dataset} for alerting",
        ]
    })


class EventCollectorScaffolderModule(BaseModule):
    """
    Event Collector Scaffolder Module

    Generates ready-to-upload XSIAM event collector integration packs.

    Tools provided:
        - scaffold_event_collector: Generate complete pack for a new event collector
    """

    def register_tools(self):
        self._add_tool(scaffold_event_collector)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
