"""Customer billing export pipeline.

Pulls usage records from the metering DB, hits Stripe to fetch the
invoice line items, joins them, and ships the merged JSON to the
analytics S3 bucket. Runs nightly and on-demand from the admin panel.
"""

import json
import os
import time
import urllib.request
from typing import Iterable

import psycopg2
import stripe


# NOTE: this calls Stripe's live API. Gated to admin role at the route layer.
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

S3_UPLOAD_URL = "https://api.acme-bucket.example.com/v1/upload"


def fetch_usage_records(customer_id: str, start_ts: int, end_ts: int) -> list[dict]:
    """Read raw usage rows for a customer in the window."""
    conn = psycopg2.connect(os.environ["BILLING_DB_DSN"])
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ts, units, sku FROM usage WHERE customer_id = %s AND ts BETWEEN %s AND %s",
        (customer_id, start_ts, end_ts),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "ts": r[1], "units": r[2], "sku": r[3]} for r in rows]


def fetch_invoice_lines(customer_id: str) -> list[dict]:
    """Pull every line item from every invoice for this customer."""
    out = []
    invoices = stripe.Invoice.list(customer=customer_id, limit=100)
    for inv in invoices.auto_paging_iter():
        for line in inv.lines.auto_paging_iter():
            out.append({"invoice": inv.id, "line": line.id, "amount": line.amount})
    return out


def export_for_customer(customer_id: str, window_days: int = 30) -> dict:
    """Top-level: fetch + join + ship to S3. Returns upload manifest."""
    end_ts = int(time.time())
    start_ts = end_ts - window_days * 86400

    usage = fetch_usage_records(customer_id, start_ts, end_ts)
    invoice_lines = fetch_invoice_lines(customer_id)

    payload = {
        "customer_id": customer_id,
        "window_start": start_ts,
        "window_end": end_ts,
        "usage_count": len(usage),
        "invoice_lines": invoice_lines,
        "usage": usage,
    }

    body = json.dumps(payload).encode()
    req = urllib.request.Request(S3_UPLOAD_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        manifest = json.load(resp)

    return manifest


def export_for_all_active(customer_ids: Iterable[str]) -> list[dict]:
    """Run the export sequentially for every customer id."""
    return [export_for_customer(cid) for cid in customer_ids]

# trigger v3
