import io
import pytest
from unittest.mock import patch, MagicMock
from weight_app import app
import json
from datetime import datetime

# Fixtures for the Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

# Test the /health endpoint
def test_health_check(client):
    with patch('weight_app.check_db_connection') as mock_check_db:
        # Simulate a successful DB connection
        mock_check_db.return_value = True
        response = client.get('/health')
        assert response.status_code == 200
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
