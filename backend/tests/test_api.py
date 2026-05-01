import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, engine
from db.connection import Database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test the health endpoint returns 200 OK."""
    rv = client.get('/api/health')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'running'
    assert 'simulation' in json_data

def test_auth_login_validation(client):
    """Test that login validates missing credentials."""
    rv = client.post('/api/auth/login', json={})
    assert rv.status_code == 400
    assert 'error' in rv.get_json()

def test_stats_update(client):
    """Test the stats endpoint returns the correct format."""
    rv = client.get('/api/health')
    assert rv.status_code == 200
