# FrontAccounting - local Docker test environment

The FrontAccounting checkout in this repository (`core/`) running in three
containers, so it can be started, stopped and re-seeded with test data in
seconds.

| service | image                     | job                                              |
|---------|---------------------------|--------------------------------------------------|
| `db`    | `mariadb:11.4`            | the FA database (volume `fa-db-data`)             |
| `php`   | `php:8.4.10-fpm-bookworm` | PHP 8.4.10 FPM with the extensions FA needs       |
| `nginx` | `nginx:1.27-alpine`       | HTTP front end, replaces the `.htaccess` rules    |

The application code is **not** baked into an image - `core/` is bind mounted,
so a `git pull` is live in the browser immediately. **Nothing in `core/` is
modified** by the containers. phpMyAdmin is baked into the PHP image.

---

## Quick start

```bash
cd /home/zoomrec/projects/frontaccounting
make up            # build + start (first time: also creates .env)
```

| | |
|---|---|
| Web UI | <http://localhost:8090> (bound to `127.0.0.1` only) |
| phpMyAdmin | <http://localhost:8090/phpmyadmin/> (same port, served via nginx) |
| Login  | `admin` or `roger` + your **production password** |
| Companies | GBC (0_), Demo Company (5_), FTSS (4_, preselected), Financial Technology Consulting Pty Ltd (6_) |
| MariaDB | `127.0.0.1:3307` - user `frontacc`, password in `.env` |

The port comes from `HTTP_PORT` in `.env` (8090 - 8080 is already taken on
this box). The stack is **not reachable from the network** by default; set
`HTTP_BIND=0.0.0.0` in `.env` if you need that.

---

## Start / stop

| command | what it does |
|---------|--------------|
| `make up` | build the php image if needed and start everything |
| `make up-dev` | same, but with the development overrides (errors on screen, opcache off) |
| `make down` | stop the containers, **keep** the database |
| `make restart` | restart php and nginx (the database keeps running) |
| `make ps` | show the state of the containers |
| `make logs` | follow the php and nginx logs (`Ctrl-C` stops following) |
| `make build` | rebuild the php image only |
| `make clean` | **destroys the database volume** - asks for confirmation |

Plain `docker compose` works as well: `docker compose up -d`,
`docker compose down`, `docker compose logs -f php`.

The database survives `make down` / `make up`. It only disappears with
`make clean` (or `docker compose down -v`).

---

## Administering

### Shell access

```bash
make shell         # bash inside the php container
make db-shell      # mariadb client, already logged in to the FA database
make pma-shell     # shell inside the phpMyAdmin container (if running)
```

Individual services:

```bash
docker compose exec php bash
docker compose exec db mariadb -ufrontacc -p frontacc
docker compose exec nginx sh
docker compose exec phpmyadmin sh
```

### Application logs

```bash
docker compose logs -f php      # php-fpm + the entrypoint
docker compose logs -f nginx    # access and error log
tail -f core/tmp/errors.log     # FrontAccounting's own error log
```

### Database

```bash
make backup                                # -> backups/frontacc-<timestamp>.sql
make restore FILE=~/frontacc.sql.gz       # import a dump
make db-shell                              # interactive SQL
```

`make restore` understands plain `.sql` and gzipped `.sql.gz` files and
repairs the `SET NAMES latin1;` that FrontAccounting writes into its own
backups (importing that as-is would encode the utf8 bytes twice).

### Passwords

```bash
make prod-passwords FILE=~/frontacc.sql.gz   # original prod password hashes back
make dev-password PASSWORD=secret COY=2      # set a known password for company 2
```

`COY` is the company index: 0 = GBC, 1 = Demo Company, 2 = FTSS,
3 = Financial Technology Consulting.

`make dev-password` overwrites the password hashes in the database - run
`make prod-passwords` afterwards to get the real ones back.

### Test users (for an LLM agent or a second pair of hands)

```bash
make test-user USER=llm_agent PASSWORD=secret COY=2
# or with a generated password:
scripts/create-test-user.sh llm_agent "" 2
```

The new user is a **clone of the existing `admin` user**: same role, same
settings, same (full) access - only the user id and the password differ.
Running the command again replaces the user, so it is safe to re-run.

**Where the credentials live:** in **`Agents.md`** in the project root. It is
mode `600` and listed in `.gitignore`, so it cannot be committed or synced to
GitHub by accident. It is a plain markdown table the agent can read:

```
| URL      | http://localhost:8090 |
| User     | llm_agent             |
| Password | ...                   |
| Company  | 2 (FTSS)              |
```

```bash
make agent-creds      # show the file
make agent-rotate     # new random password, rewritten in the file and the database
```

If you prefer the credentials outside the working tree, point
`FA_CREDENTIALS_FILE` at another path (e.g. `~/.config/frontaccounting/Agents.md`).

**Please keep the account local.** The web UI is bound to `127.0.0.1` only,
so it is not reachable from the network - only from this machine. If the
agent runs somewhere else, expose it deliberately:

```bash
# .env
HTTP_BIND=0.0.0.0
```

and put a reverse proxy with TLS and HTTP basic auth in front of it. The
database is always bound to `127.0.0.1:3307` only.

If the agent should only *read* data, the company already has an
**"Inquiries"** role (`<prefix>security_roles`, id 1) - point the new user at
it instead of the admin clone:

```sql
UPDATE 4_users SET role_id = 1 WHERE user_id = 'llm_agent';
```

### Configuration

Everything is in `.env` (gitignored, created from `.env.example`):

| variable | meaning |
|----------|---------|
| `HTTP_PORT` | port the web UI is published on |
| `HTTP_BIND` | interface the web UI is bound to - `127.0.0.1` (default) or `0.0.0.0` |
| `PMA_PORT_HOST` | port phpMyAdmin is published on (default `8081`) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_ROOT_PASSWORD` | database credentials |
| `FA_COMPANIES` | `<index>\|<name>\|<table prefix>` records, separated by `;` |
| `FA_DEF_COY` | company preselected on the login screen |
| `FA_TIMEZONE` | `date.timezone` for PHP (FA falls back to `Europe/Berlin`) |
| `FA_SECURE_ONLY` | `0` = session cookie works over plain http, `1` = https only |
| `PHP_VERSION` | PHP version of the php-fpm image (default `8.4.10`, same as production) |
| `FA_POOL_USER`, `FA_POOL_GROUP` | uid/gid the PHP pool runs as |

After changing `.env` the containers have to be **recreated** (not just
restarted) for the new values to take effect:

```bash
docker compose up -d
```

`FA_COMPANIES` must only list companies whose tables exist in the database -
picking a company without tables breaks the login screen.

### Changing the PHP version

`PHP_VERSION` in `.env` is a build argument for `docker/php/Dockerfile`
(`FROM php:${PHP_VERSION}-fpm-bookworm`).

```bash
make php-version                  # show the version of the running container
make php-switch VERSION=8.5.11    # change it, rebuild and restart
```

Or by hand:

```bash
sed -i 's|^PHP_VERSION=.*|PHP_VERSION=8.5.11|' .env
docker compose build php
docker compose up -d
```

Available tags: `8.1` … `8.6` (patch versions like `8.4.27` are more
reproducible, a minor version like `8.4` always pulls the latest patch).
See <https://hub.docker.com/_/php>.

Notes:

* The build adapts to what the base image already ships. PHP 8.5 for example
  builds `gd`/`intl`/`mysqli`/`zip`/`bcmath` differently than 8.4 and moved
  opcache, so the Dockerfile enables what is present and compiles the rest.
* `8.4.10` is the default because it matches your production server. FA
  2.4.18 was verified to run on 8.5.11 as well (login, GL inquiry, customer
  and item lists all fine), but newer minors mean more deprecation noise -
  test before switching production.
* The base image is Debian based (`bookworm`). Switching to Alpine needs
  different package names in the Dockerfile (`apk add` instead of `apt-get`).

---

## Debugging with Xdebug (VS Code)

The development stack ships with **Xdebug 3**, so you can step through the
FrontAccounting code in VS Code.

### What is needed

| where | what |
|-------|------|
| VS Code | the **PHP Debug** extension (`xdebug.php-debug`) |
| container | the `xdebug` extension - built into the image with `INSTALL_XDEBUG=1` |
| VS Code | the launch configuration **"Listen for Xdebug (fa-php container)"** (`.vscode/launch.json`) |

The normal image (`make up`) has **no** Xdebug - it is only built into the
development image.

> `.vscode/launch.json` is in `.gitignore` (it holds personal settings on
> most checkouts). A copy of the configuration is kept in
> `docker/vscode/launch.json` - copy it over if your checkout has no such
> file:

```bash
cp docker/vscode/launch.json .vscode/launch.json
```

### Usage

```bash
make up-dev          # build the image with xdebug and (re)start the stack
```

1. In VS Code: **Run and Debug** → *Listen for Xdebug (fa-php container)* → F5.
   VS Code now listens on port 9003.
2. Open <http://localhost:8090> and browse to the page you want to debug.
3. Set a breakpoint in the code (`core/`), reload the page - the request
   stops at the breakpoint.

The container dials the IDE, not the other way round (Xdebug 3 "connect"
mode), so no port has to be published. The IDE on the host is reached as
`host.docker.internal`, which the compose file maps to the docker gateway
(`extra_hosts: host-gateway`).

### Only debugging single requests

`start_with_request=yes` (the default) opens a debug session for **every**
request, which is convenient but slows the app down while the IDE is not
listening. To debug only selected requests, switch to the trigger mode:

```bash
# .env
XDEBUG_START_WITH_REQUEST=trigger
```

and add the trigger to the request - either as a query parameter
`http://localhost:8090/index.php?XDEBUG_TRIGGER=1` or as a cookie named
`XDEBUG_TRIGGER` with the value `1` (the cookie survives the redirects of
the FA login).

### Configuration

All of it lives in `.env`:

| variable | default | meaning |
|----------|---------|---------|
| `XDEBUG_CLIENT_HOST` | `host.docker.internal` | host the IDE runs on, as seen from the container |
| `XDEBUG_CLIENT_PORT` | `9003` | port the IDE listens on |
| `XDEBUG_MODE` | `develop,debug` | `debug` (step debugging), `develop` (nicer var_dump/errors), both together - `develop` is **required** by FA, it calls `xdebug_call_file()` |
| `XDEBUG_START_WITH_REQUEST` | `yes` | `yes` or `trigger` |

After changing `.env` the containers have to be recreated:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Troubleshooting

```bash
# is xdebug loaded at all?
docker compose exec php php -m | grep -i xdebug

# which settings did the entrypoint write?
docker compose exec php cat /usr/local/etc/php/conf.d/zzz-fa-xdebug.ini

# xdebug logs (connection errors) end up in the container log
docker compose logs -f php
```

| symptom | cause |
|---------|-------|
| `WARNING: FA_XDEBUG=1 but the xdebug extension is not in the image` | the image was built without `INSTALL_XDEBUG=1` - run `make up-dev` (it rebuilds) |
| the request hangs, the log says `Could not connect to the client` | the IDE does not listen on 9003, or `XDEBUG_CLIENT_PORT` differs from the port in `launch.json` |
| `Could not resolve host "host.docker.internal"` | `host-gateway` is not supported by this docker version - set `XDEBUG_CLIENT_HOST` to the gateway IP (`docker network inspect frontaccounting_default`) |
| breakpoints are not hit, the IDE shows the wrong file | `pathMappings` in `.vscode/launch.json` must map `/var/www/html` (container) to `${workspaceFolder}/core` (host) |
| the log shows `The setting 'xdebug.auto_trace' has been renamed` | `core/index.php` (upstream FA code) still calls `ini_set('xdebug.auto_trace', 1)` - harmless notice, the setting does not exist in Xdebug 3 |

---

## What the containers do behind the scenes

* `docker/php/entrypoint.sh` waits for MariaDB, renders `config_db.php` from
  the environment into `docker/generated/config_db.php` (mounted over the app
  path, so `core/` stays untouched) and fixes the permissions of the
  directories FA writes to. The rendered file is checked with `php -l`
  before it is used, so a broken configuration aborts the container instead
  of serving a 500.
* `docker/php/fa-prepend.php` is loaded through `auto_prepend_file` and
  defines `SECURE_ONLY` before the application boots. FA hard codes it to
  `true`, which makes browsers drop the session cookie over plain http.
  `define()` never overwrites an existing constant, so the application code
  does not have to be changed.
* `docker/nginx/default.conf` re-implements the rules from `core/.htaccess`:
  no directory listings, no direct access to `.inc`/`.sql`/`.log` files, no
  access to `/tmp/` or the company backup/reporting directories.
* The PHP pool runs as your own uid (`FA_POOL_USER`), so files written by the
  application stay editable and never become root owned.
* With `FA_XDEBUG=1` (development stack) the entrypoint writes
  `/usr/local/etc/php/conf.d/zzz-fa-xdebug.ini` and points Xdebug at the
  debugger on the host - see "Debugging with Xdebug" above.

---

## Known issues in this checkout (pre-existing, unrelated to Docker)

* `core/reporting/rep201.php` and `core/reporting/rep206.php` contain an
  unmatched `}` and therefore a **PHP parse error** (introduced by commit
  `312dd7a "initial merge w/error"`). Those two reports fail, the rest of
  the application is unaffected.
* `core/modules/FrontHrm` has no `lang/` directory, so
  `Domain file "./modules/FrontHrm/lang/en_US/LC_MESSAGES/en_US.po" not found`
  shows up in `core/tmp/errors.log`.
* The `core/install` directory is still reachable. Remove it (or uncomment
  the `location ^~ /install/` block in `docker/nginx/default.conf`) once the
  setup is finished.

---

## Layout

```
docker-compose.yml        the stack
docker-compose.dev.yml    development overrides
Makefile                  all the commands listed above
.env / .env.example       configuration
docker/                   images, nginx/php/mariadb configuration, entrypoints
scripts/                  env setup, restore, backup, password helpers
core/                     the FrontAccounting application (bind mounted)
```
