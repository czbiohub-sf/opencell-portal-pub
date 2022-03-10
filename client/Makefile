STAMP := $(shell date +%Y-%m-%d)

DEV_IMAGE_NAME = opencell-node-dev
BUILD_IMAGE_NAME = opencell-node-build

DEV_CONTAINER_NAME = opencell-node-dev
BUILD_CONTAINER_NAME = opencell-node-build

IMAGE_WORKDIR = /app

# default app mode (set to 'public' to prevent accidentally deploying the private app)
APP_MODE = public

# hackishly get the most recent dev image (using the fact that the tags are timestamps)
DEV_IMAGE_ID := $(shell docker images | grep $(DEV_IMAGE_NAME) | sort | tail -1 | awk '{print $$3}')


.PHONY: cleanup-dev
clean:
	-rm -rf node_modules

.PHONY: build-dev-image
build-dev-image:
	docker build --target dev -t $(DEV_IMAGE_NAME):$(STAMP) .

# install all dependencies locally, using a node container
# (a container is used to fix the versions of node and npm)
.PHONY: install-dev
install-dev:
	-docker rm -f $(DEV_CONTAINER_NAME)
	docker run -i --rm \
	--name $(DEV_CONTAINER_NAME) \
	-v $(shell pwd):$(IMAGE_WORKDIR):rw \
	$(DEV_IMAGE_ID) \
	npm install --production=false

# start the app in dev mode in a node container on port 9090
# (use 9090 to distinguish between a locally-run dev server on 8080)
# (note that the host and container ports must match in order for the websocket server to work)
.PHONY: start-dev-server
start-dev-server: 
	-docker rm -f $(DEV_CONTAINER_NAME)
	docker run -it --rm \
	--name $(DEV_CONTAINER_NAME) \
	-v $(shell pwd):$(IMAGE_WORKDIR):rw \
	-p 9090:9090 \
	$(DEV_IMAGE_ID) \
	npm run-script start-in-container

.PHONY: stop-dev-server
stop-dev-server:
	docker rm -f $(DEV_CONTAINER_NAME)

# start with clean build directories and build the build image
.PHONY: before-build
before-build:
	-rm -rf dist
	mkdir -p dist
	-docker rm -f $(BUILD_CONTAINER_NAME)
	docker build --target build -t $(BUILD_IMAGE_NAME):$(STAMP) .

.PHONY: after-build
after-build:
	-docker rm -f $(BUILD_CONTAINER_NAME)

# build the app (use -i so that `docker exec` blocks until the build command exits)
.PHONY: build
build: before-build
	docker run -i \
	--name $(BUILD_CONTAINER_NAME) \
	$(BUILD_IMAGE_NAME):$(STAMP) \
	npm run-script build -- --env appMode=$(APP_MODE)
	docker cp $(BUILD_CONTAINER_NAME):$(IMAGE_WORKDIR)/dist/. dist
	@$(MAKE) after-build

# deploy the app to the IBM cluster by copying the assets to ESS
# (first manually run `make build APP_MODE=private`)
.PHONY: deploy-to-ibm
deploy-to-ibm:
	scp -r dist/. keith@cap:/gpfs/gpfsML/ML_group/KC/nginx/data/dist
