import io
import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import mysql.connector

import unittest
from unittest.mock import patch, MagicMock
from unittest import TestCase


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app

# Fixtures for the Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

# Test the /health endpoint
def test_health_check(client):
    with patch('mysql.connector.connect') as mock_get_db, patch('time.sleep', return_value=None):  # Mock time.sleep
        # Simulate a success in the database
        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_get_db.return_value = mock_connection
    
        response = client.get('/health')
        assert response.status_code == 200
        assert json.loads(response.data.decode()) == "OK"

        # Simulate a failure in the database
        mock_get_db.side_effect = mysql.connector.Error("Connection failed")

        response = client.get('/health')
        assert response.status_code == 500
        assert json.loads(response.data.decode()) == "Failure"


# Test the /session/<id> endpoint
def test_get_session(client):
    # Mock the database connection and cursor
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()  # Correctly naming the mock connection
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
                'containers': 'container1,container2',
                'SessionId': 123
            }
        ]
        
        # Test a valid session
        response = client.get('/session/123')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['truck'] == 'Truck 1'

        # Test session not found
        mock_cursor.fetchall.return_value = []  # Simulate no session found
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
        
        # Test valid date range
        response = client.get('/weight?from=20230101000000&to=20240101000000')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['bruto'] == 1000

        # Test invalid 'from' date format
        response = client.get('/weight?from=2023-01-01&to=2024-01-01')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid 'from' date format. Use yyyymmddhhmmss."}

        # Test invalid 'to' date format
        response = client.get('/weight?from=20230101000000&to=2024-01-01')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid 'to' date format. Use yyyymmddhhmmss."}

        # Test invalid date range (from > to)
        response = client.get('/weight?from=20250101000000&to=20240101000000')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid date range. 'from' date must be before 'to' date."}

        # Test invalid filter direction
        response = client.get('/weight?filter=invalid_direction')
        assert response.status_code == 400
        assert response.json == {"error": "Invalid filter values: invalid_direction. Valid directions are 'in', 'out', 'none'."}

        # Test valid filter direction (multiple directions)
        response = client.get('/weight?filter=in,out')
        assert response.status_code == 200
        assert len(response.json) == 1

        # Test valid filter direction (single direction)
        response = client.get('/weight?filter=in')
        assert response.status_code == 200
        assert len(response.json) == 1

# Test the /unknown endpoint
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

# Test the /batch-weight endpoint
def test_batch_weight(client):
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate successful insertion of records
        mock_cursor.fetchone.return_value = [0]  # Simulate no existing container_id
        mock_cursor.rowcount = 1  # Simulate successful insertion

        # Prepare a mock CSV file
        csv_data = "id,weight,unit\ncontainer1,500,kg\ncontainer2,0,kg\n"
        csv_file = (io.BytesIO(csv_data.encode()), 'test.csv')

        response = client.post('/batch-weight', content_type='multipart/form-data', data={'file': csv_file})
        assert response.status_code == 200
        assert "message" in response.json, "Missing 'message' key in response"
        assert len(response.json["message"]) == 1, f"Expected 1 message for CSV, got: {response.json['message']}"
        assert "CSV data from test.csv processed successfully." in response.json["message"][0]

        # Prepare a mock JSON file
        json_data = [
            {"id": "container3", "weight": 1000, "unit": "lb"},
            {"id": "container4", "weight": 0, "unit": "lb"}
        ]
        json_file = (io.BytesIO(json.dumps(json_data).encode()), 'test.json')

        response = client.post('/batch-weight', content_type='multipart/form-data', data={'file': json_file})
        assert response.status_code == 200
        assert "message" in response.json, "Missing 'message' key in response"
        assert len(response.json["message"]) == 1, f"Expected 1 message for JSON, got: {response.json['message']}"
        assert "JSON data from test.json processed successfully." in response.json["message"][0]

        # Unsupported file format check
        txt_data = "id,weight,unit\ncontainer5,300,kg\n"
        txt_file = (io.BytesIO(txt_data.encode()), 'test.txt')

        response = client.post('/batch-weight', content_type='multipart/form-data', data={'file': txt_file})
        assert response.status_code == 400  # Assuming a 400 error for unsupported file type
        assert "error" in response.json, "Missing 'error' key in response"
        assert "Unsupported file format" in response.json["error"], f"Expected error message about unsupported format, got: {response.json['error']}"

        # Empty file check
        empty_csv = io.BytesIO(b'')  # Simulating an empty file
        empty_file = (empty_csv, 'empty.csv')

        response = client.post('/batch-weight', content_type='multipart/form-data', data={'file': empty_file})
        assert response.status_code == 400  # Assuming a 400 error for empty file
        assert "error" in response.json, "Missing 'error' key in response"
        assert "Empty file" in response.json["error"], f"Expected error message about empty file, got: {response.json['error']}"

# Test the /item/<id> endpoint
def test_get_item(client):
    with patch('mysql.connector.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Case 1: Truck ID found
        mock_cursor.fetchone.side_effect = [{'tara': 5000}, None]  # Found in trucks, not in containers
        mock_cursor.fetchall.return_value = [{'sessionId': 1}, {'sessionId': 2}]  # Mock session data

        response = client.get('/item/TRUCK001?from=20231101000000&to=20231117120000')
        assert response.status_code == 200
        assert response.json['id'] == 'TRUCK001'
        assert response.json['tara'] == 5000
        assert response.json['sessions'] == [1, 2]

        # Reset the mock for the next case
        mock_cursor.fetchone.side_effect = [None, {'tara': 1500}]  # Not found in trucks, found in containers
        mock_cursor.fetchall.return_value = [{'sessionId': 3}, {'sessionId': 4}]  # Mock session data

        # Case 2: Container ID found
        response = client.get('/item/C1234567890?from=20231101000000&to=20231117120000')
        assert response.status_code == 200
        assert response.json['id'] == 'C1234567890'
        assert response.json['tara'] == 1500
        assert response.json['sessions'] == [3, 4]

        # Reset the mock for the next case
        mock_cursor.fetchone.side_effect = [None, None]  # Not found in trucks or containers

        # Case 3: Item not found in either table
        response = client.get('/item/UNKNOWN?from=20231101000000&to=20231117120000')
        assert response.status_code == 404
        assert response.json == {"error": "Item not found!"}