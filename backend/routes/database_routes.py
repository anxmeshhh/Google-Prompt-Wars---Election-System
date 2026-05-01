from flask import Blueprint, jsonify, request
from db.connection import Database
import json

db_bp = Blueprint('database', __name__)

# Security note: In a real production app, this would be locked behind admin authentication.
# For demo purposes, we expose it so the user can demonstrate the hybrid architecture.

@db_bp.route('/api/database/tables', methods=['GET'])
def get_tables():
    """Return all tables in the MySQL database."""
    try:
        rows = Database.execute("SHOW TABLES")
        # Extract table names from dict (key depends on DB name, usually something like 'Tables_in_electaverse')
        tables = []
        for row in rows:
            for val in row.values():
                tables.append(val)
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@db_bp.route('/api/database/query', methods=['GET'])
def query_table():
    """Return the raw contents and schema of a specific table."""
    table = request.args.get('table')
    if not table or (not table.isalnum() and '_' not in table): # basic sanity check against SQLi
        return jsonify({'error': 'Invalid table name'}), 400
        
    try:
        # Get Schema
        schema_rows = Database.execute(f"DESCRIBE `{table}`")
        columns = [row['Field'] for row in schema_rows]
        
        # Get Data (Limit 100 for safety)
        data_rows = Database.execute(f"SELECT * FROM `{table}` LIMIT 100")
        
        # Datetimes and JSON strings might not be JSON serializable natively depending on mysql-connector config.
        # We need to sanitize the response just in case.
        sanitized_data = []
        for row in data_rows:
            sanitized_row = {}
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    sanitized_row[k] = v.isoformat()
                else:
                    sanitized_row[k] = v
            sanitized_data.append(sanitized_row)
            
        return jsonify({
            'table': table,
            'columns': columns,
            'data': sanitized_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
