"""Creates 3 fake invoices in invoices/ to test extract.py. All data is invented."""
from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "invoices"


def table(pdf, rows, widths):
    for row in rows:
        for text, w in zip(row, widths):
            pdf.cell(w, 8, str(text), border=1)
        pdf.ln()


def acme():
    # Classic layout, totals add up
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "ACME Supplies Inc.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, "Invoice #: INV-2026-0412", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Date: 2026-09-14", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    table(pdf, [
        ("Description", "Qty", "Unit price", "Amount"),
        ("Cardboard boxes (large)", 50, "1.20", "60.00"),
        ("Packing tape", 12, "2.50", "30.00"),
        ("Bubble wrap roll", 4, "15.00", "60.00"),
    ], (80, 20, 40, 40))
    pdf.ln(5)
    pdf.cell(0, 8, "TOTAL DUE: $150.00", new_x="LMARGIN", new_y="NEXT")
    pdf.output(OUT / "acme_0412.pdf")


def northwind():
    # Different layout: European date, tax line, totals add up
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, "Bill No. NW/88213        Issued 03/09/2026", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Northwind Traders Ltd", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.ln(4)
    table(pdf, [
        ("Item", "Amount"),
        ("Coffee beans 1kg x 10", "120.00"),
        ("Paper cups (pack of 500) x 2", "45.00"),
        ("Subtotal", "165.00"),
        ("Sales tax 10%", "16.50"),
        ("Grand total", "181.50"),
    ], (110, 40))
    pdf.output(OUT / "northwind_88213.pdf")


def globex():
    # Line items do NOT add up to the total (should be flagged)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=11)
    for line in [
        "GLOBEX CORPORATION",
        "-----------------------------------",
        "Invoice: GX-7731",
        "Invoice date: September 21, 2026",
        "",
        "Pallet rental ............ 200.00",
        "Forklift hours (3) ....... 135.00",
        "Delivery fee ............. 40.00",
        "",
        "TOTAL ................... 395.00",
    ]:
        pdf.cell(0, 7, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(OUT / "globex_7731.pdf")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    acme()
    northwind()
    globex()
    print("Created 3 sample invoices in", OUT)
