"""Reads every PDF in invoices/ with Gemini and writes the data to output/*.csv."""
import csv
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

ROOT = Path(__file__).parent
INVOICES = ROOT / "invoices"
OUTPUT = ROOT / "output"
MODELS = ["gemini-3.8-flash", "gemini-3.7-flash"]  # second one is used if the first is overloaded
TOLERANCE = 0.01  # max difference allowed between items + tax + fees and the total


class LineItem(BaseModel):
    description: str
    quantity: float | None
    unit_price: float | None
    amount: float


class Invoice(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: str  # YYYY-MM-DD
    currency: str
    line_items: list[LineItem]
    tax: float
    other_fees: float
    total: float


PROMPT = """Extract the data from this invoice.
- invoice_date in YYYY-MM-DD format. If the date is ambiguous (e.g. 03/09/2026), assume day/month for non-US vendors.
- line_items: only real products or services, never subtotal, tax or total rows.
- tax: total tax amount, 0 if none. other_fees: shipping or other charges that are not line items, 0 if none.
- total: the final amount due as printed on the invoice.
- currency: ISO code (USD, EUR, GBP...), guess from symbols if needed."""


def load_api_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("GEMINI_API_KEY")


def extract(client, pdf_path):
    attempts = 6
    for attempt in range(attempts):
        model = MODELS[attempt % len(MODELS)]
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type="application/pdf"),
                    PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Invoice,
                    temperature=0,
                ),
            )
            return response.parsed
        except Exception as e:
            # Only retry rate limits and server errors; other errors won't fix themselves
            code = getattr(e, "code", None)
            if attempt == attempts - 1 or (code and code != 429 and code < 500):
                raise
            print(f"  {model} failed ({code}), retrying...")
            time.sleep(5 * (attempt + 1))


def check(inv):
    calculated = round(sum(i.amount for i in inv.line_items) + inv.tax + inv.other_fees, 2)
    ok = abs(calculated - inv.total) <= TOLERANCE
    return calculated, "OK" if ok else "REVIEW: total does not match"


def main():
    key = load_api_key()
    if not key:
        sys.exit("No GEMINI_API_KEY found in .env")
    pdfs = sorted(INVOICES.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {INVOICES}")

    client = genai.Client(api_key=key)
    OUTPUT.mkdir(exist_ok=True)
    summary, items = [], []

    for pdf in pdfs:
        print(f"Reading {pdf.name}...")
        try:
            inv = extract(client, pdf)
        except Exception as e:
            summary.append({"file": pdf.name, "status": f"ERROR: {e}"})
            continue
        calculated, status = check(inv)
        summary.append({
            "file": pdf.name,
            "vendor_name": inv.vendor_name,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "currency": inv.currency,
            "line_items": len(inv.line_items),
            "tax": inv.tax,
            "other_fees": inv.other_fees,
            "calculated_total": calculated,
            "invoice_total": inv.total,
            "status": status,
        })
        for li in inv.line_items:
            items.append({
                "file": pdf.name,
                "vendor_name": inv.vendor_name,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date,
                **li.model_dump(),
            })

    write_csv(OUTPUT / "invoices.csv", summary)
    write_csv(OUTPUT / "line_items.csv", items)
    flagged = sum(1 for s in summary if s["status"] != "OK")
    print(f"\nDone: {len(summary)} invoices, {flagged} need review. Results in {OUTPUT}")


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    # utf-8-sig so Excel opens accents correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
