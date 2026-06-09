echo "Configuring backend..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# fallback if not on container
source .venv/bin/activate
pip install -r requirements.txt

echo "Applying database migrations..."
flask db upgrade

echo "Starting backend server..."
python app.py
