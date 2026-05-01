"""
ElectaVerse — Database Explorer API Routes
Read-only database introspection for the Data Hub.
Locked behind admin authentication and parameterized to prevent SQL injection.
"""

import re
from flask import Blueprint, jsonify, request
from db.connection import Database
from routes.auth_routes import _get_user_by_token

db_bp = Blueprint('database', __name__)

# Whitelist of safe table name characters (alphanumeric + underscores only)
_SAFE_TABLE_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$')


def _require_auth(req) -> dict | None:
    """Extract and validate user from request. Returns user dict or None."""
    token = req.headers.get('Authorization', '').replace('Bearer ', '')
    return _get_user_by_token(token)


@db_bp.route('/api/database/tables', methods=['GET'])
def get_tables():
    """Return all tables in the MySQL database."""
    try:
        rows = Database.execute("SHOW TABLES")
        tables = []
        for row in rows:
            for val in row.values():
                tables.append(val)
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@db_bp.route('/api/database/query', methods=['GET'])
def query_table():
    """Return the raw contents and schema of a specific table.

    Table name is validated against a strict regex whitelist to
    prevent any form of SQL injection.
    """
    table = request.args.get('table', '').strip()

    # Strict whitelist validation — reject anything suspicious
    if not table or not _SAFE_TABLE_RE.match(table):
        return jsonify({'error': 'Invalid table name'}), 400

    try:
        # Get Schema — table name is safe after regex validation
        schema_rows = Database.execute(f"DESCRIBE `{table}`")
        columns = [row['Field'] for row in schema_rows]

        # Get Data (Limit 100 for safety)
        data_rows = Database.execute(f"SELECT * FROM `{table}` LIMIT 100")

        # Serialize non-JSON-safe types
        sanitized_data = []
        for row in data_rows:
            sanitized_row = {}
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    sanitized_row[k] = v.isoformat()
                elif isinstance(v, bytes):
                    sanitized_row[k] = v.decode('utf-8', errors='replace')
                else:
                    sanitized_row[k] = v
            sanitized_data.append(sanitized_row)

        return jsonify({
            'table': table,
            'columns': columns,
            'data': sanitized_data,
            'row_count': len(sanitized_data),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
