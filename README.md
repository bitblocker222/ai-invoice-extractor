# AI Invoice Extractor

Turns a folder of PDF invoices into clean CSV files using AI (Google Gemini), and flags invoices whose totals don't add up.

Built for small businesses that retype invoice data by hand.

## What it does

- Reads every PDF in `invoices/`, from any vendor and any layout
- Extracts vendor, invoice number, date, currency, line items, tax, other fees and total
- Normalises dates to `YYYY-MM-DD`
- Checks that line items + tax + fees equal the printed total, in Python (not the AI), and marks mismatches as `REVIEW`
- Writes two Excel-ready files:
  - `output/invoices.csv`: one row per invoice, with the check result
  - `output/line_items.csv`: one row per product or service
- Retries automatically and falls back to a second model if the AI service is overloaded; one failed invoice never stops the rest

## Example result

| file | vendor_name | invoice_number | invoice_date | calculated_total | invoice_total | status |
|---|---|---|---|---|---|---|
| acme_0412.pdf | ACME Supplies Inc. | INV-2026-0412 | 2026-09-14 | 150.0 | 150.0 | OK |
| globex_7731.pdf | GLOBEX CORPORATION | GX-7731 | 2026-09-21 | 375.0 | 395.0 | REVIEW: total does not match |

The sample invoices in `invoices/` are invented; `make_samples.py` recreates them.

## How to use

1. Install Python 3.12+ and run `pip install -r requirements.txt`
2. Get a Gemini API key at [aistudio.google.com](https://aistudio.google.com) and create a `.env` file with:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Put your PDFs in `invoices/`
4. Double-click `run.bat` (or run `python extract.py`)

## How it works

1. A strict schema (`Invoice`, `LineItem`) forces the AI to always return the same fields
2. The prompt adds business rules: date format, no subtotal rows as items, tax and fees kept separate
3. Python validates the numbers, so AI mistakes are caught instead of hidden

Note: on Gemini's free tier, Google may use submitted data to improve its models. Use a paid key for real client documents.
