# FrontAccounting local Docker stack
#
#   make dev-env     create .env (with host uid/gid + random db passwords)
#   make up          build and start db + php + nginx
#   make up-dev      same, but with the development overrides
#   make logs        follow the php/nginx logs
#   make restore FILE=dump.sql   import a production dump
#   make backup      write backups/frontacc-<timestamp>.sql
#
# Note: no global "export" here - GNU make keeps the quotes of
# FA_COMPANIES="..." and would hand that value to the containers.
# "docker compose" reads .env itself.
-include .env

COMPOSE  := docker compose
COMPOSE_DEV := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
PHP_PORT ?= $(HTTP_PORT)

.PHONY: dev-env build up up-dev down restart logs ps shell db-shell pma-shell restore backup \
        prod-passwords dev-password clean php-version php-switch test-user \
        agent-creds agent-rotate xdebug

dev-env:
	@scripts/dev-env.sh

build:
	$(COMPOSE) build php

up: dev-env
	$(COMPOSE) up -d --build
	@echo "FrontAccounting: http://localhost:$(HTTP_PORT)"

up-dev: dev-env
	$(COMPOSE_DEV) up -d --build
	@echo "FrontAccounting (dev): http://localhost:$(HTTP_PORT)"

# stop the containers, keep the database
down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart php nginx

logs:
	$(COMPOSE) logs -f php nginx

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec php bash

pma-shell:
	$(COMPOSE) exec phpmyadmin sh

db-shell:
	$(COMPOSE) exec db mariadb -u$(DB_USER) -p$(DB_PASSWORD) $(DB_NAME)

restore:
	@scripts/restore-db.sh $(FILE)

backup:
	@scripts/backup-db.sh

# put the original production password hashes back into the database
prod-passwords:
	@scripts/restore-prod-passwords.sh $(FILE)

# set a known password for all users of a company (dev only)
#   make dev-password PASSWORD=secret COY=2 [USER=llm_agent]
dev-password:
	@scripts/set-dev-password.sh $(PASSWORD) $(COY) $(USER)

# create a test user as a copy of the admin user
# make test-user USER=llm_agent PASSWORD=secret COY=2
test-user:
	@scripts/create-test-user.sh "$(USER)" "$(PASSWORD)" "$(COY)"

# the credentials of the test user (stored in the gitignored Agents.md)
agent-creds:
	@scripts/agent-credentials.sh show

agent-rotate:
	@scripts/agent-credentials.sh rotate

# show the debugger status of the running container (xdebug is only in the
# development image, see docker-compose.dev.yml)
xdebug:
	@$(COMPOSE_DEV) exec -T php sh -c 'php -m | grep -i "^xdebug" || echo "xdebug is not loaded (run: make up-dev)"'
	@$(COMPOSE_DEV) exec -T php sh -c 'cat /usr/local/etc/php/conf.d/zzz-fa-xdebug.ini 2>/dev/null || echo "no xdebug ini (FA_XDEBUG is not set)"'

# show the PHP version of the running container
php-version:
	@docker compose exec -T php php -v | head -1

# switch the PHP version and rebuild, e.g. make php-switch VERSION=8.5.11
php-switch:
	@test -n "$(VERSION)" || { echo "usage: make php-switch VERSION=8.5.11"; exit 1; }
	@sed -i "s|^PHP_VERSION=.*|PHP_VERSION=$(VERSION)|" .env
	@echo "PHP_VERSION is now $(VERSION), rebuilding ..."
	$(COMPOSE) build php
	$(COMPOSE) up -d
	@$(MAKE) --no-print-directory php-version

# stop everything and throw the database volume away (DATA LOSS!)
clean:
	@echo "This deletes the database volume fa-db-data (all data is lost)."
	@read -p "Type 'yes' to continue: " a; if [ "$$a" != "yes" ]; then \
		echo "aborted - the database volume was kept"; \
	else \
		$(COMPOSE) down -v; \
		echo "database volume removed - 'make up && make restore FILE=<dump>' to start over"; \
	fi
