# Braathwaate FrontAccounting v2.4

This is a lightly modified fork of the
[Ap.Muthu FrontAccounting v2.4 github repo](https://github.com/apmuthu/frontac24.git,)
which is a current stable version of vanilla FrontAccounting (FA).
I chose to base my modifications off this fork,
but the
[Official GitHub Mirror Repo](https://github.com/FrontAccountingERP/FA/tree/master)
would also have been a good choice.

The "wwh" branch is the main repository.
The "proposed" branches are obsolete pull requests,
but are retained because
these pull requests were not integrated into the FA core.

The braathwaate modifications are mostly usability enhancements
designed to reduce the amount of clicking and scrolling
although there are also bug fixes and feature enhancements.

Following is a list of modifications
between the braathwaate fork (BF) and FA.

## wwh customizations

## Quick entry inactive support

In FA, the list of Quick entries accumulate ad infinitum.

BF supports marking the Quick entry inactive so it does not
show up in the payment list.

## Allow bank account payments on supplier direct invoice
FA restricts payment on a supplier direct invoice
to cash accounts.
For other forms of payments,
one must select "Delayed"
and enter the payment separately.

BF allows any bank account to be used for the payment,
such as a credit card.
## Allow bank accounts in POS
FA restricts payment on a customer direct invoice
to cash accounts,
because the POS setup is restricted to cash accounts.

POS systems often allow direct deposit into bank accounts,
so BF does not restrict the POS "cash sale" to cash accounts
## apportion service items; bug fixes
This mod gives the user the option on a PO to apportion service items (freight, setup charges, discounts, etc) into prices of non-service items on the PO without changing the PO order total. By apportioning these costs into item prices, they are accounted for in inventory and thus accounted for in COGS only when then items are sold. Three methods of apportionment are provided: by item quantity, line item, and line total.

additional bug fixes:

    Viewing order totals on POs with items with decimal precision greater than user decimals could be wrong because of rounding. Changes in the code reflect the method used to generate the PO, by rounding each line item to user decimals, then adding. Prior code added then rounded.

    php.ini precision could cause disabling of FA PO decimal precision for items with precise Conversion Factors. Fix was to use php.ini precision rather than disable the feature.

    credit memos for tax exempt items do not have tax gl account, and code generated a PHP warning. This did not cause any problem other than the PHP warning, because G/L was created on the remaining total.

## ajax browser sync
In FA, when a user modifies selection criteria on a FA page and AJAX updates the page, then the user clicks to another page such as via the editor, the browser back button (or FA back link) does not return to the page as the user modified it. This forces the user to reenter the selection criteria and hit the Show/Search button again.

This mod updates the browser page history when AJAX updates the page so that the back button returns to the FA page as the user modified it.
## keep reconcile on bank trans mod
When a bank transaction is modified, FA unreconciles it, even if
just the memo or date was changed.

BF retains the reconciled status.

## new combo4 autocomplete
This feature allows finding items, customers and suppliers quickly.
The configuration parameter "search_autocomplete" when set to true
changes the behavior of the Search Item List, Customer List, and
Supplier List checkboxes in the Company Setup.
When this parameter is set to "true",
an autocomplete list is updated after every character
of the search text is entered into the search box.
Thus, once the desired search item appears on the autocomplete list,
the user can make just one click to select the search item.

More keystrokes are required in in FA:
After the user enters the search text,
the user has to hit the enter key,
use the pull-down list to find the item,
and click on the item to select it.
And if the search term did not find the desired item,
the user would have to repeat the process, taking more time.

BF also makes the dropdown list work exactly the same
even when the checkbox is checked;
the checkbox just adds the ability to use the space key
to open a search box.
Otherwise the drop lists work normally.
So really there isn't any need for these checkboxes anymore.

## improve reports
FA displays an empty PDF if there is no data to display.

BF displays a message.
## Add delete link, direct link to void trans
Voiding a transaction is time-consuming and error prone in FA because
the user must provide a transaction number.

BF adds a red X icon to transactions.
Deleting transaction becomes as simple as clicking the red X
rather than having to navigate to Setup->Void.
## Add dimension to payments
FA does not dimension payments,
which causes a problem for cash basis accounting.

BF properly dimensions payments.
## allow negative quantity and amount on invoices

FA does not support invoices or payments
with negative quantities or amounts for customer refunds.
It expects that a credit memo be issued.
Nor does FA does not have the ability
to create a direct credit memo, nor does is it able to enter
purchased items and returned items on the same invoice.

BF allows this.
Besides code changes, this required altering
the "amt" field in table cust_allocations from "double unsigned"
to "double":

    mysql alter table cust_allocations modify amt double;

This has no adverse effect, and vanilla FA will also work
correctly on the altered table.

Note that negative quantities on an invoice
are returned to stock in BF.  If the customer returned an
item that cannot be returned to stock, then an inventory
adjustment will need to be made.  This is a manual operation.

## display balance in balance column and add debit/credit total

FA G/L inquiry is confusing because it displays the ending balance
under debit/credit.

BF displays the debit/credit in the proper columns
and the balance under the balance column.

## customer inquiry: display zero invoices; filter on sales type

BF displays zero invoices.
A zero invoice is often used when supplying
a customer with free product for marketing purposes.

## rename statement to register

FA uses the confusing term Bank Statement on Bank Account Inquiry
and on reports.

BF renames Bank Statement to Bank Account Inquiry and changes
reports to use Bank Register,
because data displayed is from FA
(all transactions entered)
and not from a bank statement
(all transactions processed by the bank).

## check_negative_stock allow for rounding on imprecise amounts

Decimal precise stock quantities
cause problems in FA because it is impossible to get them zeroed out.

BF assumes stock is zero when it falls below the precision
specified in Setup.

## g/l list description first to enable search by description

## BUG FIX: supplier inquiry GRN items filter by date

## FEATURE: use ajax for numeric calculations (part 1: purchasing)

FA is not a very responsive calculator or spreadsheet,
requiring the user to click an update button to do any math.

BF enables ajax on numeric text fields so that totals
are calculated as the user enters data in fields.

## add editor/delete funcs to reconcile

## allow user_transaction_days to be in future (negative)

BF allows a negative user_transaction_days in Setup so that
pages will display out into the future.

## supplier and customer name links on inquiry pages

BF makes supplier and customer names a html link
to their respective information pages
on the banking inquiry pages.
This allows one to quickly check or modify supplier/customer
information from the inquiry pages.
BF also adds the magnifying glass search icon next to these names
and this links to the supplier/customer inquiry pages.

## allow any user to edit another user transaction (disable user reference check)
BF allows a user to edit other user's transactions.

## move due date on invoice from header to footer and display only if delayed

FA displays a due date on direct supplier invoices.

BF only displays the due date if the transaction is delayed.
That is because it is meaningless if the transaction is being processed
immediately.

## remove more zero entries from Customer Balance report

The FA Customer Balance report still prints some zero entries
when no-zeros is selected.

BF fixes this problem.

## ajax enable account pull down menu on gl and bank inquiry

BF displays data without having to hit "Search".

## Scroll table instead of page

FA scrolls the whole screen on the inquiry pages.

BF scrolls the table instead of the page
and automatically positions the scroll at the latest entries.

## powderblue color on tax override

When creating a supplier invoice,
FA starts doing tax overrides after the "Update" key is pressed.
There is no visual indication that FA will stop
calculating the tax after adding another item.

BF colors the tax fields to indicate override.

## Enter key fix

FA ignores the Enter key.

BF retains the Enter key.
This means that data can be submitted with the Enter key
(as the user would expect)
and is particularly useful on the magnifying glass search popup,
because the user only needs to type the search clause
and hit enter, without having to move the mouse and click on "Search".

## Support for Enter payment on bank inquiry page

BF adds a link at the bottom of the bank inquiry page
to enter another payment.
Often a user will keep the bank inquiry page open
and continually add payments from there, rather than navigating
around through FA's pages of links.

## add total equities line to balance sheet report

The balance sheet report is missing a subtotal. It displays a Total Liabilities and Equities line at the bottom, which is a grand total of the Liabilities, Total Equity and Calculated Return.

This mod adds a Total Equities line to the report, which is equal to Total Equity and Calculated Return, which is the actual shareholder equity during the period.

With this mod, the Total Liabilities and Equities line then makes obvious sense.

## add missing spaces to rep102.php sql

report sql was broken because of missing spaces. Report works much better now.

## Update inst_lang.php

Fix for:
Illegal offset type in file: inst_lang.php at line 139

If you have error reporting enabled, you get this error when installing a language, at least manually. While the error can be ignored because the language successfully installs, it is disconcerting.

## Add frequently used dates to date picker

This mod updates the date picker to add frequently picked dates at the bottom of the date picker. Frequently, a person wants to review activity for the entire year or prior year. The current date picker does not offer these options, and requires so many clicks to to get these dates, that it is easier not to use the date picker and just enter the dates using the text interface.  This mod places these dates at the bottom of the date picker.

The Back button is replaced by clicking on the date picker again, to hide or show it (i.e. toggle). Toggling is an expected behaviour by web users, as they have become accustomed to toggling the display of select menus.

The tiny characters to go to the previous/next month/year
are replaced by "Prev/Next" and the actual year,
making it easier to click on them
because of the larger footprint.

## Add paging and scrolling to select pop-up

In FA, the select pop-up shows a (configurable) limited amount of items.
This can confuse the user into thinking that the search item does
no exist when in reality the search was limited.

BF adds scrolling and paging to the select pop-up
and no items are eliminated.
Internally,
the custom select display code was replaced with the built-in db_pager function.
This eliminates many lines of code and makes the user interface consistent
with other FA search functions.

## Name browser tab titles more specifically

Renaming tabs with differing content makes it easier for
the user to keep track of multiple open tabs.
Set the browser tab title to the value of a search element on the page
Thus when the element changes value, the browser tab title changes as well.
For example, when the user does a bank account inquiry on a certain bank
account, the bank account name shows in the tab title rather than just
"Bank Account Inquiry".   Then if the user opens another tab and does
a bank account inquiry on a different bank account, the tabs have the
bank account names rather than the duplicate title "Bank Account Inquiry".

## Change Quick Entries maintenance to use drop down menu instead of table

FA uses a table to select and modify quick entries.
If many quick entries are used,
this table quickly grows to an unmanageble size,
and it becomes time-consuming to scroll down the page to edit
the quick entry data.

BF replaces the table with a drop down menu.  Advantages are easy search,
eliminates scrolling down the page to edit the data,
presents an identical interface to other FA pages (like GL Accounts, etc),
and reduces and reuses existing code.

## G/L search on Quick Entries

FA does not offer a way to search for transactions for quick entries.

BF allows G/L search on Quick Entries.

## BUGFIX: 0004468: Cannot modify a funds transfer twice
Editing a funds transfer twice results in the message:

    The entered reference is already in use.

## BUGFIX: 0004475: Editing GJ transaction with no counterparty displays incorrect edit table

## FEATURE: Add legal terms to payment terms

FA provides a simple mechanism to add a small amount of legal text to the footer of all invoices in Setup->System and General GL Setup.

BF retains this mechanism, but also adds legal terms to payment terms, which appear on invoices using those terms. 
Payment terms often determine the content of the legal text
at the footer of the invoice.
For example, a cash invoice does not require language about
payment defaults.
In addition, it allows the legal text
to be tailored by customer or order, which is useful for different
customer types or customers located in other jurisdictions, where
differing legal text is required specific to those districts.

BF removes all the hardcoded
boiler plate footer info (e.g. Bank name, currency), relying instead
entirely on the legal text fields in setup or payment terms.
BF also checks the size of the legal text, wraps it automatically on space boundaries and reduces the font size accordingly if necessary to fit into the allocated footer space.
These changes accomodate longer legal text than is possible in FA.

This feature required a database change by adding a legal terms field to the payment_terms table.

## FEATURE: Add system preference option to sort g/l accounts by name rather than account code

## FEATURE: Add ability to enter payment memo on direct invoice

The FA direct invoice feature can create a payment as well as an invoice.
However, FA does not offer a way to directly enter the payment memo,
which is set to "<pos name> # <invoice number>".
(Although one can edit the memo afterwards).

BF adds another field to the cart, payment_info.  This field is tacked
onto the end of the FA generated memo.

## BUGFIX: 0004490: Cannot edit a quick entry transaction properly if the quick entry type changes

## FEATURE: Return to referer

The FA pencil on several inquiry forms is used to modify a transaction.
After the transaction is modified, the user has to use the back button
to get back to the inquiry form.

BF has expanded inquiry forms to have a delete link which calls the
void transaction and links to enter another payment and deposit.

This new feature returns control back to the inquiry form that calls
the modify, enter or delete links.

The result is that one can keep a bank account open to visually monitor
transactions while entering, modifying and deleting transactions.
This presents a user interface similar to the Quickbooks register,
where one can initiate all kinds of transactions from a single page.

## FEATURE: Make default account same as earlier transaction (expanded)

On Feb 2016, cambell-prince added the original feature to FA
with this pull request:
https://github.com/FrontAccountingERP/FA/pull/10.
The feature applied only to payments to suppliers made with
the Payments to Suppliers form and recalls the last bank account
used for the supplier made with this form.

BF generalizes this feature such that it applies to payments and deposits
made with Banking and General Ledger
and Customer Payments
for any person type (customer, supplier, miscellaneous, or quick entry).
It also replaces the code for Payments to Suppliers.
Thus, if a payment to a supplier is made with either interface,
the bank account from that payment will be recalled.

## 0004563 BUGFIX: rep308 costed inventory movements do not reconcile

## FEATURE: system preference option to sort item lists by description rather than by stock id

## FEATURE: Hide Process Button until add/edit is confirmed/canceled

BF removes the Process Button while payment items are being added or edited;
Otherwise, if the user neglects to confirm, the work is lost unexpectantly.

## 00457 BUGFIX: sales order cancel goes ahead even if user clicks cancel on confirmation

## FEATURE: confirm price changes on invoice entry when changing suppliers

During invoice entry, FA automatically changes prices (and the supplier reference)
if the supplier is changed.
This allows one to compare prices between suppliers,
if the suppliers have up-to-date price information.

However, often the user is doing simple purchase order entry and
may have forgotten to set the correct supplier beforehand.
Changing the supplier name afterwards results in lost work.

BF provides a pop-up confirmation whether the user wants to reprice
the order or simply change the supplier.

## FEATURE: reissue customer invoice

FA offers very limited editing of customer invoices, just the invoice date.

BF retains the FA editor (in case the user just wants to change the date),
but also adds a Reissue function icon to the
customer transactions page.
The reissue function
voids the invoice and delivery and opens a series of editors
to recreate the invoice: sales order modification; delivery; and invoice.
Thus the user can make any possible change, addition, deletion
to the invoice and still retain the old invoice number.

Although an FA user could accomplish the same thing by
manually performing the voids and navigating to the same pages,
the BF Reissue process requires only clicking on a single icon
to initiate the process.

Note that a void of an auto generated delivery in FA clears all quantities
in the sales order whereas BF retains the order quantities,
which is consistent with a void of a manually created delivery.

I am also not keen on FA voiding an auto generated delivery
from a void of direct invoice, because a void of a manual invoice
does not void the deliveries, creating confusion for the user.
However, I left BF unchanged on this point.
Ideally there should be a popup on a void of an invoice asking
if the deliveries and sales orders should be voided or left as is.

## FEATURE: create new customer option during sales invoice entry

It is convenient to be able to create a new customer during order entry.
While FA offers this ability with the F2 function key,
operation isn't quite optimal,
requiring a function key to activate a popup,
finding and selecting New Customer in the drop down menu,
creating the customer,
closing the popup,
and selecting the newly created customer in the customer list.

BA retains this feature but also adds "New Customer" to the customer list
and a "Create New Customer" link whenever "New Customer" is selected.
This requires only one additional click to create the customer
and after the customer is created, the order entry screen
is set to the new customer.

## FEATURE: add new customer defaults for sales type, sales area, tax group
## FEATURE: remember last bank account transfer
## BUGFIX:  0004594: Tax group still showing when inactive
## FEATURE: tax groups can be sales or purchases only
## BUGFIX: 0004601: memo line not cleared after enter new payment item
## BUGFIX:  0004606: Cannot add a zero price to an item with a purchase price in inventory adjustment
## BUGFIX:  0004614: Allocated journal entry payment shows in red (overdue) on customer transactions"
## BUGFIX: 0004617: memo undefined at line 206 core/manufacturing/includes/db/work_order_costing_db.inc"

## FEATURE: manufacturing pick list costs from g/l accounts

The FA basic manufacturing feature supports two g/l additional costs,
named "Labour" and "Overhead".

In BF, these are renamed "Cost 1" and "Cost 2",
because these accounts can be used for any G/L account,
so the FA names can be inappropriate.

BF provides a link to open up the G/L account
and pick list costs from the G/L account.
This can assist in determining which costs are applicable
to the manufacturing process.

BF removes the restriction that a BOM is required,
to support simple manufacturing without components in inventory.
For example, a volume of a manufactured item
could be expanded by adding water
without any BOM needed.

## FEATURE: add "No Counterparty" to Counterparty drop-down list

In FA, General Journal forces the use of a counterparty if
the G/L account is listed in a supplier as an accounts payable account
or in a customer as an accounts receivable account.

This is inconsistent with Payments/Deposits, which allow posting
to these G/L accounts using Miscellaneous or Quick Entry.

BF adds "No Counterparty" to the Counterparty drop-down list
in General Journal.

## FEATURE: add ability to copy BOM to another parent

## FEATURE: find and mark inactive items during popup search

In FA, all of the popup searches (magnifying glass)
return inactive items
(except for the item search which does not ever show inactive items).
There is no checkbox option to configure this;
the checkbox option on the main page applies only to the dropdown list
on that page.

We have found that this is extremely confusing to our users.
Users who rely on the popup search
are unable to find inactive items
and the customer and supplier lists are bloated with inactive entries.

BF displays inactive entries, but marked with (INACTIVE)
in the name or description and sorted to the bottom of the list.
All lists function identically in this manner.

As a design note, the idea of yet another inactive checkbox was discarded
because the length of search lists in the popup tend to be short,
so the addition of marked inactive entries at the bottom
do not bloat the lists.
Additionally,
we have found that users often resort
to using the popup list when they are unable to find an item,
and do not guess that the reason is because the item was marked inactive.

## do not show bank deposits when invoice filter is selected in supplier inquiry
## add viewport for improved mobile device support

BA adds declares a viewport to size the FA view to the device size.
This should have no effect on the desktop, but makes it
easier to use FA on a mobile device.
While this is far from creating a truly mobile FA,
it is a good interim measure.

(One reason to use FA on a mobile device is the ability to
use the device touchscreen to sign PDF invoices generated by FA.
This is easy to do by adding the Adobe Sign & Fill App (or comparable)
to the device.)

See http://frontaccounting.com/punbb/viewtopic.php?pid=30616#p30616.

## select next item after item delete

When an item is deleted in FA, the item list is refreshed
and positioned to "New Item".
This is not very helpful, because often the user wants to delete
more than one item.
In addition,
it is useful to redisplay the list with the deleted item removed,
giving the user satisfaction that the item is indeed gone.

BF positions the list to the next item after the deleted one
and selects that item.
Thus, if the user is deleting a series of consecutive inventory items,
the user just has to keep hitting the delete key
to delete them.

## FEATURE: basic manufacturing option to specify single component/no bom

It is useful to be able to transfer one item to another
so that a single manufactured item can be made in different ways
(part substitution).

For example, item A is a manufactured item offered for sale,
item B is a manufactured item built one way
and item C is a manufactured item built another way (different BOM).
Thus to replenish the supply of item A,
either B or C can be transferred to item A.

Item transfer can also be used to manufacture of items sized by volume.
For example, manufactured item A is the blend of item B and item C;
where volume(A) = volume(B) + volume(C).

One could accomplish this in FA Basic Manufacture
by creating a BOM of item A with component ratios,
but this often difficult to calculate in practice,
especially if the exact blend is inconsequential.
Often one wants to add ingredients on a step-wise basis
before the final quantity is known.

A better way is to use FA Advanced Manufacture
which can assign issues
("ingredients" or "raw materials") to a work order.
It does not require a BOM.
For manufactured items where the intermediate result is
not desired, each ingredient can be added
and the quantity produced can be edited.

However, if intermediate results are needed
(such as if the item is needed in another manufacturing process),
the item needs to be produced and another
workorder is required for further work.

Multiple workorders for a single item
are also needed when the manufacturer
wants to monitor the manufactured item in inventory rather than
as works-in-progress in the manufacturing tab.
For example,
a legal authority monitoring alcohol inventory does not want to
see alcohol disappear from inventory when it is used as an ingredient
in Advanced Manufacture for a blended item that has not yet
been produced.

So when multiple workorders are needed to add each ingredient,
an easier process is desired.

FA Basic Manufacturing requires a BOM and does not
allow the assignment of issues.

BF modifies Basic Manufacturing
so that a BOM is not required, just like for Advanced Manufacture.
BF allows the addition of a single issue
to support item transfer and one ingredient per workorder.
Using this approach,
Basic Manufacturing is simpler than Advanced Manufacturing
when a single item/multiple workorder production process is desired.

This is strictly a user-interface change.
No database changes were needed.

## FEATURE: allow component stock item to be changed on BOM

FA disallows changing the component stock item during BOM edit. 
If one wants to change a stock item on a BOM, one has to delete it
and then add the desired one.
This is slow and error prone.

BF allows changing the component stock item.

## FEATURE: inactive checkbox and zero inventory button on inv. adjustments

BF adds a checkbox to show inactive inventory items and
a "zero inventory" button to zero out an inventory item.
