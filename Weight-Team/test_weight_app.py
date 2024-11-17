import pytest
from unittest.mock import patch, MagicMock
from weight_app import app
import json

# Fixtures for the Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

# Test the /health endpoint
def test_health_check(client):
    # Mock the database connection function
    with patch('weight_app.check_db_connection') as mock_check_db:
        # Simulate a successful DB connection
        mock_check_db.return_value = True
        response = client.get('/health')
        assert response.status_code == 200
        
        # Parse the JSON response and compare the content
        assert json.loads(response.data.decode()) == "OK"  # Expect the raw string "OK" as the JSON content

        # Simulate a failed DB connection
        mock_check_db.return_value = False
        response = client.get('/health')
        assert response.status_code == 500
        assert json.loads(response.data.decode()) == "Failure"  # Expect the raw string "Failure" as the JSON content

# Test the /session/<id> endpoint
def test_get_session(client):
    # Mock the database cursor and connection
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate a session found in the database
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'direction': 'in',
                'truck': 'Truck 1',
                'bruto': 1000,
                'truckTara': 200,
                'neto': 800,
                'containers': 'container1,container2'
            }
        ]
        
        response = client.get('/session/123')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['truck'] == 'Truck 1'

        # Simulate a session not found
        mock_cursor.fetchall.return_value = []
        response = client.get('/session/999')
        assert response.status_code == 404
        assert response.json == {"error": "Session not found"}

# Test the /weight endpoint
def test_get_weights(client):
    # Mock the database cursor and connection
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate successful query results
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'direction': 'in',
                'bruto': 1000,
                'neto': 800,
                'produce': 'Produce 1',
                'containers': 'container1,container2'
            }
        ]
        
        response = client.get('/weight?from=20230101000000&to=20240101000000')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['bruto'] == 1000

        # Test invalid date format
        response = client.get('/weight?from=2023-01-01&to=2024-01-01')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid 'from' date format. Use yyyymmddhhmmss."}

        # Test invalid filter direction
        response = client.get('/weight?filter=invalid_direction')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid filter values: invalid_direction. Valid directions are 'in', 'out', 'none'."}

# Test the /unknown endpoint (not defined in the app above, but assume it exists)
def test_get_unknown_weights(client):
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate an empty result (no unknown weights)
        mock_cursor.fetchall.return_value = []
        response = client.get('/unknown')
        assert response.status_code == 200
        assert response.json == []

        # Simulate some unknown weights (NULL values)
        mock_cursor.fetchall.return_value = [
            {'container_id': 'container1'},
            {'container_id': 'container2'}
        ]
        response = client.get('/unknown')
        assert response.status_code == 200
        assert response.json == ['container1', 'container2']
