DB_CONTAINER_NAME = opencell-staging-db
API_CONTAINER_NAME = opencell-staging-backend
NGINX_CONTAINER_NAME = opencell-staging-frontend

USER_DIR := $(shell cd ~/ && pwd)
STAMP := $(shell date +%Y-%m-%d)
DUMP_FILENAME = $(STAMP)-opencelldb-prod-dump

# note: do not use spaces after the commas in the if statement
define env_or_else_default
$(if $($(1)),$($(1)),$(2))
endef

# APP_ENV determines the docker-compose configs to use
# (note there is not actually a local prod config;
# the if-else statement is included only to mirror the aws makefile)
DEFAULT_APP_ENV = staging
APP_ENV := $(call env_or_else_default,APP_ENV,$(DEFAULT_APP_ENV))
ifeq ($(APP_ENV), staging)
export COMPOSE_FILE = docker-compose.base.yaml:docker-compose.staging.yaml
else ifeq ($(APP_ENV), prod)
export COMPOSE_FILE = docker-compose.base.yaml:docker-compose.prod.yaml
endif

.PHONY: show-app-env
show-app-env:
	@echo $(APP_ENV)

.PHONY: compile-frontend-assets
compile-frontend-assets:
	cd ../../client && $(MAKE) build

.PHONY: build
build: down
	docker-compose build
	docker-compose up -d

.PHONY: build-frontend
build-frontend:
	docker-compose build frontend
	docker-compose up -d

.PHONY: build-backend
build-backend:
	docker-compose build backend
	docker-compose up -d

.PHONY: deploy
deploy: compile-frontend-assets build

.PHONY: deploy-frontend
deploy-frontend: compile-frontend-assets build-frontend

.PHONY: deploy-backend
deploy-backend: build-backend

.PHONY: start
start:
	docker-compose start

.PHONY: stop
stop:
	docker-compose stop

.PHONY: down
down:
	-docker-compose down

# also drops named docker volumes (e.g. the db-data volume used for database data)
.PHONY: down-hard
down-hard:
	-docker-compose down --volumes

.PHONY: restart-nginx
restart-nginx:
	docker exec $(NGINX_CONTAINER_NAME) nginx -s reload

.PHONY: restore-db
restore-db:
	# first stop the entire app to drop any existing database connections
	# (open connections prevent `pg_restore --clean` below from dropping the database)
	docker-compose stop

	# start only the database container and call pg_restore
	docker start $(DB_CONTAINER_NAME)
	docker exec -i $(DB_CONTAINER_NAME) \
		pg_restore \
			--username opencell \
			-d postgres \
			--clean \
			--create \
			--no-owner \
			--no-privileges \
			/home/dumps/$(DUMP_FILENAME)

	# now start the rest of the app
	docker-compose start
