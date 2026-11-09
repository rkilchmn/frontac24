#!/usr/bin/env python3
"""Build the Salary supplier-invoice import CSV from the CPF PDFs in work/.

Each PDF yields one salary invoice with a single line item:
    item code SAL, description "Net Salary", quantity 1,
    price = Ordinary Wages ($) − Employee CPF ($)

Example: Ordinary Wages 2,000.00 − Employee CPF 400.00 = Net Salary 1,600.00.

Reference handling (import_transactions module): the first line of each
invoice leaves `reference` empty so the importer assigns the next free
reference.

pypdf is required: run with the project venv python (.venv/bin/python3).
"""
import csv
import glob
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "supplier_invoice_salary.csv")

from pypdf import PdfReader

SUPPLIER_ID = "5"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
     "Sep", "Oct", "Nov", "Dec"], start=1)}


def extract_text(path):
    r = PdfReader(path)
    return "\n".join((pg.extract_text() or "") for pg in r.pages)


def supp_ref_of(text, path):
    """The supplier reference is the PDF's 'Month Paid For' field, e.g. 'NOV 2025'."""
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


def net_salary(text, path):
    """Net Salary = Ordinary Wages ($) − Employee CPF ($), parsed from the
    'Total Amount' line of the per-employee table.

    Line layout:
    [CPF To Be Paid, SDL To Be Paid, Employer CPF, Employee CPF,
     Ordinary Wages, Additional Wages, -, -]
    """
    m = re.search(r'^Total Amount\s+(.*)$', text, re.M)
    if not m:
        raise ValueError("no 'Total Amount' line in %s" % os.path.basename(path))
    toks = m.group(1).split()
    if len(toks) < 7:
        raise ValueError("cannot parse 'Total Amount' line in %s" % os.path.basename(path))

    def f(s):
        return float(s.replace(",", ""))

    employee_cpf = f(toks[3])
    ordinary_wages = f(toks[4])
    return ordinary_wages - employee_cpf


rows = []
pdfs = sorted(glob.glob(os.path.join(WORK, "*.pdf")))
for pdf in pdfs:
    text = extract_text(pdf)
    supp_ref = supp_ref_of(text, pdf)
    date = invoice_date_of(text, pdf)
    salary = net_salary(text, pdf)

    pdf_basename = os.path.basename(pdf)
    rows.append([
        SUPPLIER_ID,                      # supplier name
        "",                               # reference: empty -> next free reference
        supp_ref,                         # e.g. 'NOV 2025' (Month Paid For)
        date,                              # invoice date (payment date)
        date,                              # due date = invoice date
        "SAL",                             # item code: Net Salary
        "Net Salary",                      # item description
        "1",                               # quantity
        "%.2f" % salary,                   # price = Ordinary Wages − Employee CPF
        "", "", "", "",                    # location, dimensions, comments
        pdf_basename                       # attachment: PDF filename
    ])


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
