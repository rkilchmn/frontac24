# docker/

Configuration for the local FrontAccounting test stack.

The full documentation - how to start, stop and administer the containers -
is in **[../DOCKER.md](../DOCKER.md)**.

```
php/Dockerfile          php-fpm image with the FA extensions
php/php.ini             php configuration
php/php-dev.ini         development overrides
php/php-fpm.conf        FPM pool configuration
php/entrypoint.sh       waits for the db, renders config_db.php, fixes permissions
php/fa-prepend.php      SECURE_ONLY override (no application change needed)
nginx/default.conf      nginx server block
mysql/conf.d/fa.cnf     MariaDB server configuration
generated/              config_db.php (generated at startup) + the original
vscode/launch.json      reference copy of the VS Code debug configuration
                        (.vscode/launch.json itself is gitignored)
```

Xdebug (development stack only) is not a file in here: the extension is
built into the image with `INSTALL_XDEBUG=1` and the settings are rendered
at startup into `/usr/local/etc/php/conf.d/zzz-fa-xdebug.ini`.
