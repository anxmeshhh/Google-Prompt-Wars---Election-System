#!/bin/bash
set -e

echo "ElectaVerse Backend Starting..."

echo "Running database seed..."
python db/seed.py || echo "seed.py failed (DB may not be ready yet)"

echo "Running content seed..."
python db/seed_content.py || echo "seed_content.py failed (non-critical)"

echo "Starting Gunicorn..."
exec gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 --timeout 120 app:app
