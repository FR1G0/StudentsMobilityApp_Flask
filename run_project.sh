#!/bin/bash

# Exit on error
set -e

# 1. Database
echo "Building and starting database container..."
docker build -t overseas-db .
if [ "$(docker ps -aq -f name=overseas-db-container)" ]; then
    docker start overseas-db-container
else
    docker run -d --name overseas-db-container -p 5432:5432 overseas-db
fi

# 2. Backend
echo "Configuring backend..."
cd backend
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
echo "Applying database migrations..."
flask db upgrade
echo "Starting backend server..."
python app.py &
BACKEND_PID=$!
cd ..

# 3. Frontend
echo "Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
# Cleanup backend process on exit
trap "kill $BACKEND_PID" EXIT

npx ng serve --configuration=development
