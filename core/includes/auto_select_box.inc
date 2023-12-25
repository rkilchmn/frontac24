<?php
include_once($path_to_root . "/includes/Mobile_Detect.php");
global $SysPrefs;

// Make sure the auto select box for searching not causing trouble.
if (@$SysPrefs->auto_select_box == true) {
	// Disable auto select box on mobile device because it has problem
	// with the soft keyboard input.
	$detect = new Mobile_Detect();
	if ($detect->isMobile()) {
		$SysPrefs->auto_select_box = false;
	}
}
