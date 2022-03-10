FROM node:16.12.0 as base

WORKDIR /app


# 'dev' image is just a node container
FROM base as dev

CMD ["/bin/bash"]


# 'build' image is used to build the app
FROM base as build

# copy both package.json and package-lock.json
COPY package*.json ./

RUN npm install

COPY . .

CMD ["/bin/bash"]