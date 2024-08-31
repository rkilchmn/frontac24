-- delta database from stock 2.4 to this branch --

INSERT IGNORE INTO `0_sys_prefs` VALUES
	('tax_bank_payments', 'setup.company', 'tinyint', 1, '0');

ALTER TABLE `6_tax_groups` 
ADD COLUMN `no_sale` TINYINT(1) NOT NULL DEFAULT '0',
ADD COLUMN `no_purchase` TINYINT(1) NOT NULL DEFAULT '0';

