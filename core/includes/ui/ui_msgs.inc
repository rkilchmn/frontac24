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

/**
 * Helper function to add messages directly to the global messages array.
 * This bypasses trigger_error() which is deprecated for E_USER_ERROR in PHP 8.4.
 * 
 * @param int $errno Error type (E_USER_ERROR, E_USER_WARNING, E_USER_NOTICE)
 * @param string $msg Error message
 */
function _add_message($errno, $msg)
{
	global $messages, $SysPrefs, $cur_error_level;
	
	// Initialize messages array if not set
	if (!isset($messages) || !is_array($messages)) {
		$messages = array();
	}
	
	// Get backtrace if debug mode is enabled
	$bt = '';
	if (isset($SysPrefs) && $SysPrefs->go_debug > 1) {
		// Check if get_backtrace function exists (from errors.inc)
		if (function_exists('get_backtrace')) {
			$bt = get_backtrace(true, 2); // Skip 2 levels: this function and caller
		}
	}
	
	// Get file and line from backtrace for context
	$file = null;
	$line = null;
	$trace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 2);
	if (isset($trace[1])) {
		$file = isset($trace[1]['file']) ? $trace[1]['file'] : null;
		$line = isset($trace[1]['line']) ? $trace[1]['line'] : null;
	}
	
	// Add message to the array (same format as error_handler in errors.inc)
	$messages[] = array($errno, $msg, $file, $line, $bt);
}

function display_error($msg, $center=true)
{
	// PHP 8.4 deprecates trigger_error() with E_USER_ERROR
	// Use direct message collection instead
	_add_message(E_USER_ERROR, $msg);
}

function display_notification($msg, $center=true)
{
	// Use direct message collection for consistency
	_add_message(E_USER_NOTICE, $msg);
}

function display_warning($msg, $center=true)
{
	// Use direct message collection for consistency
	_add_message(E_USER_WARNING, $msg);
}

function display_notification_centered($msg)
{
	display_notification($msg, true);
}

function display_caption($msg)
{
	echo "<caption>$msg</caption>\n";
}

function display_heading($msg)
{
	echo "<center><span class='headingtext'>$msg</span></center>\n";	
}

function display_heading2($msg)
{
	echo "<center><span class='headingtext2'>$msg</span></center>\n";	
}

function display_note($msg, $br=0, $br2=0, $extra="")
{
	for ($i = 0; $i < $br; $i++)
		echo "<br>";
	if ($extra != "")	
		echo "<center><span $extra>$msg</span></center>\n";	
	else	
		echo "<center><span>$msg</span></center>\n";	
	for ($i = 0; $i < $br2; $i++)
		echo "<br>";
}

function stock_item_heading($stock_id)
{
	if ($stock_id != "") 
	{
		$result = db_query("SELECT description, units FROM ".TB_PREF."stock_master WHERE stock_id=".db_escape($stock_id));
        $myrow = db_fetch_row($result);
        
    	display_heading("$stock_id - $myrow[0]"); 
    	$units = $myrow[1];
    	display_heading2(_("in units of : ") . $units);        	
	}
}

