<?php
/**
 * Container level override for FrontAccounting's hard coded
 *   define('SECURE_ONLY', true);
 * in includes/session.inc.
 *
 * define() never overwrites an already defined constant, it only emits a
 * warning - so defining the constant here, before the application boots, is
 * enough to get a session cookie that works over plain http (the container
 * serves http on localhost, and the SECURE_ONLY flag would otherwise make
 * browsers refuse the cookie).
 *
 * The behaviour is controlled by the FA_SECURE_ONLY environment variable:
 *   0 / false / no / off -> session cookie is not flagged "secure"
 *   1 / true  / yes / on  -> session cookie is flagged "secure" (https only)
 *   unset                 -> the constant is not defined here at all and
 *                            FrontAccounting keeps its original behaviour
 *
 * This file is wired up with auto_prepend_file in php.ini, so nothing inside
 * the FrontAccounting source tree has to be modified.
 */

$fa_secure_only = getenv('FA_SECURE_ONLY');

if ($fa_secure_only !== false && $fa_secure_only !== '' && !defined('SECURE_ONLY')) {
	$fa_secure_only = !in_array(strtolower($fa_secure_only), array('0', 'false', 'no', 'off'));

	if (!$fa_secure_only) {
		define('SECURE_ONLY', false);

		// silence the "Constant SECURE_ONLY already defined" warning that
		// includes/session.inc triggers - only that one warning, everything
		// else keeps the normal error handling
		set_error_handler(function ($errno, $errstr) {
			return ($errno === E_WARNING)
				&& strpos($errstr, 'Constant SECURE_ONLY already defined') !== false;
		});
	}
}
