<?php
/**
 * phpMyAdmin configuration for FrontAccounting
 * Uses 'config' auth_type for auto-login
 */
declare(strict_types=1);

$cfg['blowfish_secret'] = 'fa-docker-stack-' . (getenv('DB_PASSWORD') ?: 'change_me');

$i = 0;
$i++;
$cfg['Servers'][$i]['auth_type'] = 'config';
$cfg['Servers'][$i]['host'] = getenv('PMA_HOST') ?: 'db';
$cfg['Servers'][$i]['port'] = getenv('PMA_PORT') ?: '3306';
$cfg['Servers'][$i]['user'] = getenv('PMA_USER') ?: 'frontacc';
$cfg['Servers'][$i]['password'] = getenv('PMA_PASSWORD') ?: '';
$cfg['Servers'][$i]['connect_type'] = 'tcp';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = false;

$cfg['Servers'][$i]['hide_db'] = '^(information_schema|performance_schema|mysql|sys)$';

$cfg['ShowChgPassword'] = false;
$cfg['ShowCreateDb'] = false;
$cfg['ShowPhpInfo'] = false;
$cfg['ShowServerInfo'] = false;
$cfg['LoginCookieValidity'] = 3600;