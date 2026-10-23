# The PHP version is a build argument, change it in .env:
#   PHP_VERSION=8.5.12     (matches the production server)
#   PHP_VERSION=8.5        (latest 8.5 patch release)
# Available: https://hub.docker.com/_/php
ARG PHP_VERSION=8.5.12
FROM php:${PHP_VERSION}-fpm-bookworm

# FrontAccounting needs:
#   mysqli  - the only DB driver FA uses (includes/db/connect_db_mysqli.inc)
#   gd      - tcpdf image handling + item picture thumbnails
#   intl    - collation / number formatting used by the reporting module
#   zip     - module/extension package handling
#   bcmath  - accounting arithmetic
#   curl    - modules/bank_import hooks
#   mbstring - already in the base image
#   pdo_mysql - modules/sgw_import, whose ORM (Anorm) talks to the database over PDO
#
# The base image ships a different set of pre-built extensions in every PHP
# release (PHP 8.5 for example builds gd/intl/mysqli/zip/bcmath itself and
# no longer ships opcache), so only what is really missing is installed.
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		libpng-dev \
		libjpeg62-turbo-dev \
		libfreetype6-dev \
		libwebp-dev \
		libzip-dev \
		libicu-dev \
		default-mysql-client \
		gettext-base \
	; \
	ext_dir="$(php -r 'echo ini_get("extension_dir");')"; \
	for ext in mysqli pdo_mysql gd intl zip bcmath; do \
		if php -m | grep -qix "$ext"; then \
			echo ">>> $ext is already enabled"; \
		elif [ -f "$ext_dir/$ext.so" ]; then \
			echo ">>> enabling the pre-built $ext"; \
			docker-php-ext-enable "$ext"; \
		else \
			echo ">>> building $ext from source"; \
			if [ "$ext" = "gd" ]; then \
				docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp; \
			fi; \
			docker-php-ext-install -j"$(nproc)" "$ext"; \
		fi; \
	done; \
	if [ -f "$ext_dir/opcache.so" ]; then \
		docker-php-ext-enable opcache; \
	else \
		echo ">>> opcache is not shipped with this PHP version, skipping"; \
	fi; \
	rm -rf /var/lib/apt/lists/*; \
	php -v; \
	php -m | grep -iE "^(mysqli|pdo_mysql|gd|intl|zip|bcmath|mbstring|curl|Zend OPcache)$" | sort

# Xdebug - development only.
#
# The debugger is not part of the normal image: it is built only when the
# INSTALL_XDEBUG build argument is 1 (docker-compose.dev.yml sets it), so the
# image started by "make up" stays free of it.
#
# The sources are taken from the GitHub release instead of PECL: the
# pecl.php.net channel answers with a 504 from some networks, the release
# tarball is stable and can be pinned to a version.
ARG INSTALL_XDEBUG=0
ARG XDEBUG_VERSION=3.4.3
RUN set -eux; \
	if [ "$INSTALL_XDEBUG" != "1" ]; then \
		echo ">>> xdebug not requested (INSTALL_XDEBUG=$INSTALL_XDEBUG)"; \
		exit 0; \
	fi; \
	cd /tmp; \
	curl -fsSL -o xdebug.tar.gz "https://github.com/xdebug/xdebug/archive/refs/tags/${XDEBUG_VERSION}.tar.gz"; \
	tar -xzf xdebug.tar.gz; \
	cd "xdebug-${XDEBUG_VERSION}"; \
	phpize; \
	./configure --enable-xdebug; \
	make -j"$(nproc)"; \
	make install; \
	# xdebug is a zend extension: docker-php-ext-enable detects that and
	# writes "zend_extension=xdebug" into the conf.d
	docker-php-ext-enable xdebug; \
	rm -rf /tmp/xdebug.tar.gz "/tmp/xdebug-${XDEBUG_VERSION}"; \
	php -r 'echo "xdebug ", phpversion("xdebug"), " installed\n";'

# FA is a classic PHP app: everything is served through index.php in the
# document root, no rewrites required.
WORKDIR /var/www/html

COPY php.ini /usr/local/etc/php/conf.d/zz-fa.ini
COPY php-fpm.conf /usr/local/etc/php-fpm.d/zz-fa.conf
COPY fa-prepend.php /usr/local/etc/fa/fa-prepend.php
COPY entrypoint.sh /usr/local/bin/fa-entrypoint
RUN chmod +x /usr/local/bin/fa-entrypoint

# The pool itself runs as www-data (already present in the base image).
# The entrypoint starts php-fpm as root so it can fix ownership of the
# writable FA directories, then the pool drops to www-data.
RUN set -eux; \
	mkdir -p /var/lib/php/sessions /etc/fa; \
	chown -R www-data:www-data /var/lib/php/sessions /etc/fa; \
	chmod 1777 /var/lib/php/sessions

EXPOSE 9000

ENTRYPOINT ["/usr/local/bin/fa-entrypoint"]
CMD ["php-fpm", "-F"]
