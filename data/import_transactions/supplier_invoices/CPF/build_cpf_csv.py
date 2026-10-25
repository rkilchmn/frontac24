#!/usr/bin/env python3
"""Build the CPF (Central Provident Fund Board) supplier-invoice import CSV
from the PDFs in work/.

Every non-zero line item in a PDF becomes its own CSV line with the matching
item code (CPF-CCO, CPF-CCS, CPF-CEO, CPF-LPI), mirroring supplier invoice
#188 which carries the maximum of four line items. The invoice total is
calculated by the import from the sum of the line item amounts.

Reference handling (import_transactions module): the first line of each
invoice leaves `reference` empty so the importer assigns the next free
reference; the further lines of the same invoice use `+` in the reference
column to continue the document.

pypdf is required: run with the project venv python (.venv/bin/python3).
"""
import csv
import glob
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "supplier_invoice_cpf.csv")

from pypdf import PdfReader

SUPPLIER_ID = "3"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
     "Sep", "Oct", "Nov", "Dec"], start=1)}


def extract_text(path):
    r = PdfReader(path)
    return "\n".join((pg.extract_text() or "") for pg in r.pages)


def supp_ref_of(text, path):
    """The supplier reference is the PDF's 'Month Paid For' field, e.g. 'APR 2026'."""
    m = re.search(r'Month Paid For\s*:\s*([A-Za-z]{3,4} \d{4})', text)
    if not m:
        raise ValueError("no 'Month Paid For' in %s" % os.path.basename(path))
    return m.group(1)


def invoice_date_of(text, path):
    """Invoice date = actual payment date: the Deduction Date (direct debit)
    when present, otherwise the Submission Date (PayNow QR). Normalised to
    dd/mm/yyyy."""
    m = re.search(r'Deduction Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
    if m:
        d, mo, y = m.group(1).split('/')
        return "%02d/%02d/%s" % (int(d), int(mo), y)
    m = re.search(r'Submission Date\s*:\s*([A-Za-z]{3,4} \d{1,2}, \d{4})', text)
    if m:
        mon, day, y = m.group(1).replace(",", " ").split()
        return "%02d/%02d/%s" % (int(day), MONTHS[mon.lower()], y)
    raise ValueError("no Deduction or Submission Date in %s" % os.path.basename(path))


def table1_amount(text, label, path):
    """Amount ($) of a line in the PDF's charge breakdown table."""
    m = re.search(re.escape(label) + r'\s+([\d,]+(?:\.\d+)?)', text)
    if not m:
        raise ValueError("no %r line in %s" % (label, os.path.basename(path)))
    return float(m.group(1).replace(",", ""))


def employer_employee_cpf(text, path):
    """Employer CPF and Employee CPF from the 'Total Amount' line of the
    per-employee table. Line layout:
    [CPF To Be Paid, SDL To Be Paid, Employer CPF, Employee CPF, Ordinary Wages, Additional Wages, -, -]"""
    m = re.search(r'^Total Amount\s+(.*)$', text, re.M)
    if not m:
        raise ValueError("no 'Total Amount' line in %s" % os.path.basename(path))
    toks = m.group(1).split()
    if len(toks) < 4:
        raise ValueError("cannot parse 'Total Amount' line in %s" % os.path.basename(path))

    def f(s):
        return float(s.replace(",", ""))

    return f(toks[2]), f(toks[3])


rows = []
pdfs = sorted(glob.glob(os.path.join(WORK, "*.pdf")))
# Keep only the last 3 (APR, MAY, JUN 2026) — the earlier ones are already in the system
pdfs = pdfs[-3:]
for pdf in pdfs:
    text = extract_text(pdf)
    supp_ref = supp_ref_of(text, pdf)
    date = invoice_date_of(text, pdf)
    lpi = table1_amount(text, "CPF Late Payment Interest", pdf)
    sdl = table1_amount(text, "Skills Development Levy (SDL)", pdf)
    employer_cpf, employee_cpf = employer_employee_cpf(text, pdf)

    items = [
        ("CPF-CCO", employer_cpf),
        ("CPF-CCS", sdl),
        ("CPF-CEO", employee_cpf),
        ("CPF-LPI", lpi),
    ]

    first = True
    pdf_basename = os.path.basename(pdf)
    for item_code, amount in items:
        if amount <= 0:
            continue
        rows.append([
            SUPPLIER_ID,                      # supplier_id (Central Provident Fund Board)
            "" if first else "+",             # reference: empty -> next free, '+' continues the invoice
            supp_ref,                         # 'APR 2026' (Month Paid For)
            date,                              # invoice date (payment date)
            date,                              # due date = invoice date (Cash Only terms, 0 days)
            item_code,                         # item code, e.g. CPF-CCO
            "",                                # item_description: left empty, the item master fills it
            "1",                               # quantity
            "%.2f" % amount,                   # price (the invoice total is the sum of these)
            "", "", "", "",                    # location (first of company), dimensions, comments
            pdf_basename if first else ""      # attachment: PDF filename on first line of invoice
        ])
        first = False

def make_zip(zip_path, work_dir):
    """Create a zip file containing all PDFs from the work directory."""
    pdfs = sorted(glob.glob(os.path.join(work_dir, "*.pdf")))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for pdf in pdfs:
            z.write(pdf, os.path.basename(pdf))
    print("wrote", zip_path, "with", len(pdfs), "PDFs")


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
make_zip(zip_path, WORK)

print("invoices:", len(pdfs), "lines:", len(rows))
print("wrote", OUT)
