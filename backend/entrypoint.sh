#!/bin/bash
# ElectaVerse â€” Docker Entrypoint
# Seeds the database on every startup (uses ON DUPLICATE KEY, so idempotent)
# Then starts Gunicorn with eventlet for WebSocket support.

set -e

echo "ðŸ—³ï¸  ElectaVerse Backend Starting..."

# Seed constituencies, booths, and simulation config
echo "ðŸ“¦ Running database seed..."
python db/seed.py || echo "âš ï¸  seed.py failed (DB may not be ready yet, app will retry)"

# Seed election timeline and voter guide content
echo "ðŸ“¦ Running content seed..."
python db/seed_content.py || echo "âš ï¸  seed_content.py failed (non-critical)"

echo "ðŸš€ Starting Gunicorn..."
exec gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 --timeout 120 app:app
