#!/usr/bin/env python3
"""Build the Zero1 supplier-invoice import CSV from the PDFs in work/.

One CSV line per invoice. A multi-item invoice collapses to a single line
item priced at the PDF's "Amount Due"; the per-line breakdown
(each line's description and price, ;-separated) goes into the
invoice-level description/memo (the CSV comments column).
"""
import csv
import glob
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "supplier_invoice_zero1.csv")

from pypdf import PdfReader

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
     "Sep", "Oct", "Nov", "Dec"], start=1)}
DATE_RE = re.compile(r'^(\d{1,2}) ([A-Za-z]{3}) (\d{4})$')


def dd_mm_yyyy(s):
    m = DATE_RE.match(s.strip())
    if not m:
        raise ValueError("cannot parse date: %r" % s)
    return "%02d/%02d/%s" % (int(m.group(1)), MONTHS[m.group(2).lower()], m.group(3))


def extract_text(path):
    r = PdfReader(path)
    return "\n".join((pg.extract_text() or "") for pg in r.pages)


def date_after(lines, marker, max_scan=8):
    """First plain date line within max_scan lines after the marker line."""
    for i, line in enumerate(lines):
        if marker in line:
            for j in range(i + 1, min(i + 1 + max_scan, len(lines))):
                s = lines[j].strip()
                m = DATE_RE.match(s)
                if m and not s.endswith("-"):
                    return dd_mm_yyyy(s)
            break
    return ""


def amount_due(lines):
    """Net payable: the value on the line after the 'Amount Due' label."""
    for i, line in enumerate(lines):
        if "Amount Due" in line:
            if i + 1 < len(lines):
                m = re.match(r'^\s*([\d.]+)', lines[i + 1])
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
    return None


def charge_items(lines):
    """(description, exact_amount_str, abs_value) for each non-zero charge line.

    The exact amount string keeps the PDF's full precision (and sign); the
    abs_value is used for the net-payable price.
    """
    out = []
    for line in lines:
        s = line.strip()
        if not (re.match(r'^[GZ]\s', s) and " to " in s):
            continue
        toks = s.split()
        if len(toks) < 3:
            continue
        try:
            val = float(toks[-1])
        except ValueError:
            continue
        if val == 0:
            continue
        desc = " ".join(toks[1:-1])
        out.append((desc, toks[-1], abs(val)))
    return out


def fmt2(x):
    return "%.2f" % x


rows = []
pdfs = sorted(glob.glob(os.path.join(WORK, "*.pdf")))
for pdf in pdfs:
    parts = os.path.basename(pdf).replace(".pdf", "").split("_")
    cand = [t for t in parts if re.fullmatch(r"\d{16}", t)]
    if not cand:
        raise ValueError("no 16-digit invoice number in %s" % os.path.basename(pdf))
    inv_no = cand[0]

    # Short attachment filename: inv_no + short date (under 60 chars)
    # e.g., "1010000000563684_15Jun2025.pdf" = 29 chars
    m_date = re.search(r'_(\d{2}[A-Za-z]{3}\d{4})_(\d{2}[A-Za-z]{3}\d{4})', os.path.basename(pdf))
    if m_date:
        start_date = m_date.group(1)  # e.g., 15Jun2025
    else:
        start_date = "unknown"
    short_name = "%s_%s.pdf" % (inv_no, start_date)

    text = extract_text(pdf)
    lines_all = text.splitlines()
    bill_date = date_after(lines_all, "Bill Date")
    due_date = date_after(lines_all, "Payment will be deducted on")

    # The invoice price is the PDF's "Amount Due" (the net amount Zero1
    # will deduct). In pypdf's text the figure sits on the line after the
    # "Amount Due" label.
    pdf_total = amount_due(lines_all)

    items = charge_items(lines_all)
    if not items:
        total_str = ("%.2f" % pdf_total) if pdf_total is not None else "0"
        items = [("Zero1 monthly charge", total_str, abs(float(total_str)))]

    if len(items) == 1:
        # A single PDF line becomes the line item's description/memo; the
        # line amount is the PDF's "Amount Due".
        desc = "%s %s" % (items[0][0], items[0][1])
        comments = ""
    else:
        # Multiple PDF lines: one line item at the PDF "Amount Due"; the
        # per-line breakdown (each line's description and price,
        # ;-separated) goes into the invoice-level description/memo (the
        # comments column).
        desc = "Zero1 monthly charge"
        comments = ";".join("%s %s" % (d, a_str) for d, a_str, _ in items)

    if pdf_total is not None:
        price = pdf_total
    else:
        price = items[0][2] if len(items) == 1 else sum(abs_v for _, _, abs_v in items)

    rows.append([
        "6",              # supplier_id (Zero1 Pte Ltd)
        "",                # reference: left blank -> the importer assigns the next free one
        inv_no,           # supp_ref
        bill_date,
        due_date,
        "EXP-TELC",       # item_code
        desc,             # line item description
        "1",              # quantity
        fmt2(price),      # price (the PDF "Amount Due", 2 decimals)
        "", "", "",       # location, dimension_id, dimension2_id
        comments,         # invoice-level description/memo
        short_name,       # attachment: short PDF filename (under 60 chars)
    ])

with open(OUT, "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["supplier_id", "reference", "supp_ref", "date", "due_date",
                 "item_code", "item_description", "quantity", "price",
                 "location", "dimension_id", "dimension2_id", "comments",
                 "attachment"])
    for row in rows:
        w.writerow(row)

# Create the companion zip file with the same base name as the CSV
zip_path = os.path.splitext(OUT)[0] + ".zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for pdf in pdfs:
        parts = os.path.basename(pdf).replace(".pdf", "").split("_")
        cand = [t for t in parts if re.fullmatch(r"\d{16}", t)]
        inv_no = cand[0] if cand else "unknown"
        m_date = re.search(r'_(\d{2}[A-Za-z]{3}\d{4})_(\d{2}[A-Za-z]{3}\d{4})', os.path.basename(pdf))
        start_date = m_date.group(1) if m_date else "unknown"
        short_name = "%s_%s.pdf" % (inv_no, start_date)
        z.write(pdf, short_name)
    print("wrote", zip_path, "with", len(pdfs), "PDFs")

print("invoices:", len(pdfs), "lines:", len(rows))
print("wrote", OUT)
