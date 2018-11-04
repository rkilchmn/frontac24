<?php
/**********************************************************************
    Copyright (C) FrontAccounting, LLC.
	Released under the terms of the GNU General Public License, GPL, 
	as published by the Free Software Foundation, either version 3 
	of the License, or (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
    See the License here <http://www.gnu.org/licenses/gpl-3.0.html>.
***********************************************************************/
$page_security = 'SA_TAXREP';
// ----------------------------------------------------------------
// $ Revision:	2.0 $
// Creator:	Joe Hunt
// date_:	2005-05-19
// Title:	Sales Summary Report
// ----------------------------------------------------------------
$path_to_root="..";

include_once($path_to_root . "/includes/session.inc");
include_once($path_to_root . "/includes/date_functions.inc");
include_once($path_to_root . "/includes/data_checks.inc");
include_once($path_to_root . "/gl/includes/gl_db.inc");

//------------------------------------------------------------------


print_sales_summary_report();

function getTaxTransactions($from, $to, $fromcust, $tax_id, $daily)
{
	$fromdate = date2sql($from);
	$todate = date2sql($to);

	$sql = "SELECT d.debtor_no, d.name AS cust_name, d.tax_id, t.name AS tax_group, dt.type, dt.trans_no,  dt.tran_date,
			CASE WHEN dt.type=".ST_CUSTCREDIT." THEN (ov_amount+ov_freight+ov_discount)*-1 
			ELSE (ov_amount+ov_freight+ov_discount) END *dt.rate AS total,
			CASE WHEN dt.type=".ST_CUSTCREDIT." THEN (ov_amount+ov_discount)*-1 
			ELSE (ov_amount+ov_discount) END *dt.rate AS nf
		FROM ".TB_PREF."debtor_trans dt
			LEFT JOIN ".TB_PREF."debtors_master d ON d.debtor_no=dt.debtor_no
			LEFT JOIN ".TB_PREF."cust_branch br ON br.branch_code=dt.branch_code
			LEFT JOIN ".TB_PREF."tax_groups t ON br.tax_group_id=t.id
		WHERE (dt.type=".ST_SALESINVOICE." OR dt.type=".ST_CUSTCREDIT.") ";
	if ($fromcust)
		$sql .= "AND dt.debtor_no=".db_escape($fromcust);
	if ($tax_id)
		$sql .= "AND tax_id<>'' ";
	$sql .= "AND dt.tran_date >=".db_escape($fromdate)." AND dt.tran_date<=".db_escape($todate);

        // Add in any journaled gl sales transactions
        // from default sales account without customers

        $sales_account = db_escape(get_company_pref('default_sales_act'));
        $sql .= " UNION ALL SELECT '-1' AS debtor_no, CONCAT($sales_account, ' ', account_name) AS cust_name, '' as tax_id, '{Default Sales Account Journaled Transactions}' AS tax_group, '0' AS type, '0' AS trans_no, tran_date, -amount AS total, -amount AS nf
            FROM ".TB_PREF."gl_trans gl
            LEFT JOIN ".TB_PREF."chart_master cm on account_code=$sales_account
            WHERE account = $sales_account
	    AND tran_date >=".db_escape($fromdate)." AND tran_date<=".db_escape($todate)
            ." AND !(type =".ST_SALESINVOICE." OR type=".ST_CUSTCREDIT.") ";
        $sql .= " ORDER BY tax_group, cust_name"; 
        if ($daily)
		$sql .= ", tran_date";

    return db_query($sql,"No transactions were returned");
}

function getTaxes($type, $trans_no)
{
	$sql = "SELECT included_in_price, SUM(CASE WHEN trans_type=".ST_CUSTCREDIT." THEN -amount ELSE amount END * ex_rate) AS tax
		FROM ".TB_PREF."trans_tax_details WHERE trans_type=$type AND trans_no=$trans_no GROUP BY included_in_price";

    $result = db_query($sql,"No transactions were returned");
    if ($result !== false)
    	return db_fetch($result);
    else
    	return null;
}    	

//----------------------------------------------------------------------------------------------------

function print_sales_summary_report()
{
	global $path_to_root;
	
	$from = $_POST['PARAM_0'];
	$to = $_POST['PARAM_1'];
    $fromcust = $_POST['PARAM_2'];
	$tax_id = $_POST['PARAM_3'];
	$daily = $_POST['PARAM_4'];
	$comments = $_POST['PARAM_5'];
	$orientation = $_POST['PARAM_6'];
	$destination = $_POST['PARAM_7'];
	if ($tax_id == 0)
		$tid = _('No');
	else
		$tid = _('Yes');

	if ($destination)
		include_once($path_to_root . "/reporting/includes/excel_report.inc");
	else
		include_once($path_to_root . "/reporting/includes/pdf_report.inc");
	$orientation = ($orientation ? 'L' : 'P');

	$dec = user_price_dec();

	$rep = new FrontReport(_('Sales Summary Report'), "SalesSummaryReport", user_pagesize(), 9, $orientation);

	$params =   array( 	0 => $comments,
						1 => array('text' => _('Period'), 'from' => $from, 'to' => $to),
						2 => array(  'text' => _('Tax Id Only'),'from' => $tid,'to' => ''));

	$cols = array(0, 130, 180, 270, 350, 430, 550);

	$headers = array(_('Customer'), _('Tax Id'), _('Total ex. Freight'), _('Total ex. Tax'), _('Tax'));
	$aligns = array('left', 'left', 'right', 'right', 'right');
    if ($orientation == 'L')
    	recalculate_cols($cols);

	$rep->Font();
	$rep->Info($params, $cols, $headers, $aligns);
	$rep->NewPage();
	
	$totalnet = 0.0;
	$totalnf = 0.0;
	$totaltax = 0.0;
	$st_totalnet = 0.0;
	$st_totalnf = 0.0;
	$st_totaltax = 0.0;
	$transactions = getTaxTransactions($from, $to, $fromcust, $tax_id, $daily);

	$rep->TextCol(0, 4, _('Balances in Home Currency'));
	$rep->NewLine(2);
	
	$custno = 0;
	$tax = $total = $nf = 0;
	$custname = $tax_id = "";
    $tax_group = "";
    $tran_date = "";
    $prior_nf = 0;
    $prior_total = 0;
    $prior_tax = 0;
	while ($trans=db_fetch($transactions))
	{
        if ($daily
            && $tran_date != $trans['tran_date'])
        {
            if ($tran_date != "") {
                if ($prior_total != $total) {
                    $rep->TextCol(1, 2,	$tran_date);
                    $rep->AmountCol(2, 3, $nf-$prior_total, $dec);
                    $rep->AmountCol(3, 4, $total-$prior_total, $dec);
                    $rep->AmountCol(4, 5, $tax-$prior_tax, $dec);
                    $rep->NewLine();
                    $prior_nf = $nf;
                    $prior_total = $total;
                    $prior_tax = $tax;
                }
            }
            $tran_date = $trans['tran_date'];
        }

        if (($tax_group != ""
            && $tax_group != $trans['tax_group'])
		    || ($custno != $trans['debtor_no'])) {

			if ($custno != 0)
			{
				$rep->TextCol(0, 1, $custname);
				$rep->TextCol(1, 2,	$tax_id);
				$rep->AmountCol(2, 3, $nf, $dec);
				$rep->AmountCol(3, 4, $total, $dec);
				$rep->AmountCol(4, 5, $tax, $dec);
				$totalnf += $nf;
				$totalnet += $total;
				$totaltax += $tax;
                $st_totalnf += $nf;
                $st_totalnet += $total;
                $st_totaltax += $tax;
				$prior_total = $prior_tax = $prior_nf = $total = $tax = $nf = 0;
				$rep->NewLine();

				if ($rep->row < $rep->bottomMargin + $rep->lineHeight)
				{
					$rep->Line($rep->row - 2);
					$rep->NewPage();
				}
			}
			$custno = $trans['debtor_no'];
			$custname = $trans['cust_name'];
			$tax_id = $trans['tax_id'];

            if ($tax_group != ""
                && $tax_group != $trans['tax_group']) {
                $rep->Font('bold');
                $rep->NewLine();
                $rep->Line($rep->row + $rep->lineHeight);
                $rep->TextCol(0, 2, $tax_group);
                $rep->AmountCol(2, 3, $st_totalnf, $dec);
                $rep->AmountCol(3, 4, $st_totalnet, $dec);
                $rep->AmountCol(4, 5, $st_totaltax, $dec);
                $rep->Line($rep->row - 5);
                $rep->Font();
                $rep->NewLine();
                $rep->NewLine();
                $st_totalnf=0;
                $st_totalnet=0;
                $st_totaltax=0;
            }
            $tax_group = $trans['tax_group'];

		}	
		$taxes = getTaxes($trans['type'], $trans['trans_no']);
		if ($taxes != null)
		{
			if ($taxes['included_in_price'])
				$trans['total'] -= $taxes['tax'];
			$tax += $taxes['tax'];
		}	
		$total += $trans['total']; 
		$nf += $trans['nf']; 

	}
	if ($custno != 0)
	{
		$rep->TextCol(0, 1, $custname);
		$rep->TextCol(1, 2,	$tax_id);
		$rep->AmountCol(2, 3, $total, $dec);
		$rep->AmountCol(3, 4, $tax, $dec);
		$totalnf += $nf;
		$totalnet += $total;
		$totaltax += $tax;
		$rep->NewLine();

                $rep->Font('bold');
                $rep->NewLine();
                $rep->Line($rep->row + $rep->lineHeight);
                $rep->TextCol(0, 2, $tax_group);
                $rep->AmountCol(2, 3, $st_totalnf + $nf, $dec);
                $rep->AmountCol(3, 4, $st_totalnet + $total, $dec);
                $rep->AmountCol(4, 5, $st_totaltax + $tax, $dec);
                $rep->Line($rep->row - 5);
                $rep->Font();
                $rep->NewLine();
	}
	$rep->Font('bold');
	$rep->NewLine();
	$rep->Line($rep->row + $rep->lineHeight);
	$rep->TextCol(0, 2,	_("Total"));
	$rep->AmountCol(2, 3, $totalnf, $dec);
	$rep->AmountCol(3, 4, $totalnet, $dec);
	$rep->AmountCol(4, 5, $totaltax, $dec);
	$rep->Line($rep->row - 5);
	$rep->Font();

	$rep->End();
}

