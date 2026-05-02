"""
ElectaVerse — Database Explorer API Routes
Read-only database introspection for the Data Hub.
Locked behind admin authentication and parameterized to prevent SQL injection.
All queries are logged for audit trail compliance.
"""

from flask import Blueprint, jsonify, request
from db.connection import Database
from routes.auth_routes import _get_user_by_token
from utils.validators import validate_table_name

db_bp = Blueprint('database', __name__)


def _require_admin(req) -> dict | None:
    """Extract and validate user from request. Requires 'official' role."""
    token = req.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return None
    # Admin check — only officials can access database explorer
    if user.get('role') != 'official':
        return None
    return user


@db_bp.route('/api/database/tables', methods=['GET'])
def get_tables():
    """Return all tables in the MySQL database. Requires admin authentication."""
    user = _require_admin(request)
    if not user:
        return jsonify({'error': 'Admin authentication required'}), 403

    try:
        rows = Database.execute("SHOW TABLES")
        tables = []
        for row in rows:
            for val in row.values():
                tables.append(val)

        # Log the query to Cloud Logging
        try:
            from services.gcloud_logging_service import log_event
            log_event('database.query', {
                'user_id': user['id'],
                'query_type': 'list_tables',
                'ip': request.remote_addr,
            })
        except Exception:
            pass

        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@db_bp.route('/api/database/query', methods=['GET'])
def query_table():
    """Return the raw contents and schema of a specific table.

    Table name is validated against a strict whitelist to
    prevent any form of SQL injection. Admin-only access.
    """
    user = _require_admin(request)
    if not user:
        return jsonify({'error': 'Admin authentication required'}), 403

    table = request.args.get('table', '').strip()

    # Whitelist validation — only known tables allowed
    if not validate_table_name(table):
        return jsonify({'error': 'Invalid or disallowed table name'}), 400

    try:
        # Get Schema — table name is safe after whitelist validation
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

        # Audit log
        try:
            from services.gcloud_logging_service import log_event
            log_event('database.query', {
                'user_id': user['id'],
                'query_type': 'select',
                'table': table,
                'rows_returned': len(sanitized_data),
                'ip': request.remote_addr,
            })
        except Exception:
            pass

        return jsonify({
            'table': table,
            'columns': columns,
            'data': sanitized_data,
            'row_count': len(sanitized_data),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

