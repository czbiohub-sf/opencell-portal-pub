DEV_DB_CONTAINER_NAME = opencelldb-dev
TEST_DB_CONTAINER_NAME = opencelldb-test


.PHONY: init
init:
	pip install -r requirements.txt

.PHONY: setup-develop
setup-develop:
	pip install -e .'[dev]'
	pre-commit install

.PHONY: pre-commit
pre-commit:
	pre-commit run --all-files

.PHONY: lint
lint:
	flake8 . --count --statistics --exit-zero
	python -m pylint ./opencell

.PHONY: test
test:
	pytest -v --ignore ./client/node_modules

.PHONY: start-test-db
start-test-db: drop-test-db
	docker create \
	--name $(TEST_DB_CONTAINER_NAME) \
	-e POSTGRES_PASSWORD=password \
	-e POSTGRES_DB=opencelldb \
	-p 5433:5432 \
	-v $(PWD):/home/opencell:rw \
	postgres
	docker start $(TEST_DB_CONTAINER_NAME) && sleep 2

.PHONY: drop-test-db
drop-test-db:
	-docker rm --force $(TEST_DB_CONTAINER_NAME);

.PHONY: start-pgadmin
start-pgadmin:
	docker pull dpage/pgadmin4:latest
	docker run -d \
	-p 8081:80 \
	-e PGADMIN_DEFAULT_EMAIL=opencell@czbiohub.org \
	-e PGADMIN_DEFAULT_PASSWORD=password \
	--name pgadmin \
	dpage/pgadmin4
