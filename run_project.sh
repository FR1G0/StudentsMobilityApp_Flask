#!/bin/bash

# Exit on error
set -e

### NOTE: check dependencies

if ! command -v docker &> /dev/null ; then
	echo "[ERROR] missing docker, please install docker."
	exit 1
fi

###  NOTE: building

# 1. Database
echo "[DOCKER] Building database (postgres) container..."
docker build -t overseas-db .

# 2. Backend
echo "[DOCKER] Building backend (flask+sqlalchemy) server ..."
docker build -t overseas-backend -f backend/Dockerfile ./backend

# 3. Frontend
echo "[DOCKER] Building frontend (angularjs) server ..."
docker build -t overseas-frontend -f frontend/Dockerfile ./frontend

###  NOTE: running

# create network to allow comms between the containers
docker network create overseas-network 2>/dev/null || true

# named volume so database state survives container recreation
docker volume create overseas-db-data > /dev/null

# database
echo "[DOCKER] Running database (postgres) container..."
if [ "$(docker ps -aq -f name=overseas-db-container)" ]; then
    docker start overseas-db-container
else
    docker run -d \
		--name overseas-db-container \
		--network overseas-network \
		-p 5432:5432 \
		-v overseas-db-data:/var/lib/postgresql/data \
		overseas-db
fi

# the backend runs the migrations on startup (schema + seed data + triggers),
# so postgres must accept connections before the backend starts
echo "[DOCKER] Waiting for the database to accept connections..."
for i in $(seq 1 30); do
	if docker exec overseas-db-container pg_isready -U myuser -d overseas_db &> /dev/null ; then
		break
	fi
	if [ "$i" -eq 30 ]; then
		echo "[ERROR] database did not become ready in time."
		exit 1
	fi
	sleep 1
done

# backend
echo "[DOCKER] Running backend (flask+sqlalchemy) container..."
if [ "$(docker ps -aq -f name=overseas-backend-container)" ]; then
    docker start overseas-backend-container
else
    docker run -d \
		--name overseas-backend-container \
		--network overseas-network \
		-p 5000:5000 \
		-e DATABASE_URL=postgresql://myuser:123@overseas-db-container:5432/overseas_db \
		-e SECRET_KEY="${SECRET_KEY:-supersecret}" \
		-e JWT_SECRET="${JWT_SECRET:-}" \
		overseas-backend
fi

# frontend
echo "[DOCKER] Running frontend (angularjs) container..."
if [ "$(docker ps -aq -f name=overseas-frontend-container)" ]; then
    docker start overseas-frontend-container
else
    docker run -d \
		--name overseas-frontend-container \
		--network overseas-network \
		-p 4200:4200 \
		overseas-frontend
fi

echo "[DONE] frontend: http://localhost:4200 - backend API: http://localhost:5000"
