# Zero1 Supplier Invoices — Extraction & Import Playbook

## Supplier
- Zero1 Pte Ltd — supplier_id `6` in FrontAccounting (company FTSS, prefix `4_`)
- Zero1 account no. `30039007`, UEN `201705239R`
- Invoice numbers: 16-digit, series prefix (101/102/103…) + sequence, e.g. `1010000000509221`

## Current files (this directory)
| File | Content |
|---|---|
| `build_zero1_csv.py` | Regenerates the import CSV from the 12 PDFs in `work/`: one CSV line per invoice, `price` = the PDF's "Amount Due" (2 decimals). A single-line PDF becomes the line item's `item_description` (description + exact amount). A multi-line PDF becomes one line item at the "Amount Due", with the per-line breakdown (each line's description and price, `;`-separated) in the `comments` column = the invoice-level description/memo. Run with `.venv/bin/python build_zero1_csv.py`. |
| `supplier_invoice_zero1.csv` | **Import file** — the 12 invoices, one line per invoice (12 lines). References are left blank, so the importer auto-assigns the next free reference on the real (non-trial) import. |
| `work/` | The 12 real Zero1 invoice PDFs (Jun 2025 – May 2026). |
| `test_data/` | Older single-invoice test files (2026 dates): `supplier_invoice_zero1.csv` (production record trans_no 247, not re-importable), `_test` / `_mock` (import verified OK). |

## Multi-invoice CSV rules (why the earlier trial failed)
- The import processes one invoice at a time: a line with a **new reference** closes the invoice being collected and opens a new one; a line with `+` continues the current invoice.
- A **blank** reference calls `Refs->get_next()`, which during a trial run always returns the same "next" reference (nothing is written, so the counter never advances). Result: every new invoice's first line resolved to the same reference → "The supplier and the supplier's invoice reference have to be the same for all lines of an invoice".
- **Fix:** each new invoice's first line must carry an explicit unique FA document reference matching the refline pattern `{NNN}/{YYYY}` (regex `^\d+/<year>$`). Continuation lines use `+`.
- Reference numbers come from `4_reflines` (pattern `{001}/{YYYY}`) and used numbers from `4_refs`; the next free per year was computed from those tables.

## Negative prices / credits
- The import check rejects `price < 0`. Invoice `1010000001111313` (15/04/2026–14/05/2026) has a credit line priced `-3.7769` (6u plan downgrade adjustment); the per-line breakdown in `comments` keeps the PDF's exact signed value.
- The invoice `price` is the PDF's **"Amount Due"** — the net amount Zero1 deducts (5.00 for `1010000001111313`), not the gross "Total Current Charges" (15.90).

## Comments length (PO Comments column)
- The production `6_purch_orders.Comments` column is short (~255 chars). HTML in the comment (e.g. `<br>`) gets entity-encoded by the DB layer (`&lt;br&gt;`), inflating the stored length and causing MySQL error 1406 "Data too long for column 'comments'".
- Fix (user): drop `<br>` separators entirely (the UI does not render them as newlines) and join the per-line breakdown with `;` instead. The comment is now plain text, 234 chars max on the longest invoice (line 11), which fits the column with no encoding overhead.

## Extraction (real run)
1. Save a new Zero1 invoice PDF into `work/`.
2. Extract the text with the project venv:
   ```bash
   cd /home/zoomrec/projects/frontaccounting
   .venv/bin/python -c "
   from pypdf import PdfReader
   r = PdfReader('<pdf file>')
   print('\n'.join(p.extract_text() or '' for p in r.pages))"
   ```
3. Map the PDF fields to the 12-column supplier-invoice import CSV:
   - `supplier_id` = `6`
   - `reference` = explicit next free reference for the invoice date's year (blank refs fail in trial runs)
   - `supp_ref` = the PDF invoice number; if that number is already imported, use a fresh number (bump the series: 101 → 102 → 103 → …)
   - `date` = "Bill Date" (DD/MM/YYYY)
   - `due_date` = the "Payment will be deducted on <date>" line (DD/MM/YYYY)
   - `item_code` = `EXP-TELC`
   - `item_description` = the charge line, e.g. "6u - Monthly Fee 15 Jun to 14 Jul"
   - `quantity` = `1`
    - `price` = the PDF's "Amount Due" (the net deductible amount), not "Total Current Charges"
   - `location`, `dimension_id`, `dimension2_id`, `comments` = blank

## Import rules
- System date format is DD/MM/YYYY. Open fiscal year is 2025-07-01 → 2026-06-30 (closed=0); all 12 invoices (15/07/2025–15/06/2026) fall inside it.
- Run a trial (dry) run first via the FA `import_transactions` module, then the real import.
- After the real import, verify in `4_supp_trans` (12 new ST_SUPPINVOICE rows) and in `4_refs` (the 12 new references are recorded).
