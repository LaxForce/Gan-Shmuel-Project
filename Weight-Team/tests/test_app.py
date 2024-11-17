# import unittest
# from flask import Flask
# from weight_app import app  # Assuming your Flask app is in the file app.py (adjust as needed)

# class FlaskAppTestCase(unittest.TestCase):_
    
#     @classmethod
#     def setUpClass(cls):
#         """Run once before all tests."""
#         cls.app = app.test_client()  # Create a test client for your Flask app
#         cls.app.testing = True  # Enable testing mode
    
#     def test_home_route(self):
#         """Test the root route (GET /)"""
#         response = self.app.get('/')
#         self.assertEqual(response.status_code, 200)
#         self.assertIn(b"Welcome to the Truck Weighing API!", response.data)
    
#     def test_health_check_route(self):
#         """Test the health check route (GET /health)"""
#         response = self.app.get('/health')
#         self.assertEqual(response.status_code, 200)  # Assuming the DB is available
#         self.assertIn(b"OK", response.data)
    
#     def test_health_check_failure(self):
#         """Test the health check route (GET /health) when DB fails"""
#         # Simulate database failure by making the check_db_connection return False
#         # You could mock the DB connection to make it fail, but for simplicity,
#         # we assume the default check passes.
#         response = self.app.get('/health')
#         self.assertEqual(response.status_code, 500)
#         self.assertIn(b"Failure", response.data)
    
#     def test_get_weights_route(self):
#         """Test the /weight route (GET /weight) with query params"""
#         response = self.app.get('/weight?from=20230101000000&to=20230101235959&filter=in')
#         self.assertEqual(response.status_code, 200)
#         # Check if the response contains expected structure
#         data = response.get_json()
#         self.assertIsInstance(data, list)  # The response should be a list
        
#     def test_get_session_route(self):
#         """Test the /session/<id> route (GET /session/<id>)"""
#         # Simulate a valid session ID (you can replace 123 with an actual ID in your DB)
#         response = self.app.get('/session/123')
#         self.assertEqual(response.status_code, 200)
#         data = response.get_json()
#         self.assertIsInstance(data, list)  # Should return a list of sessions
        
#         # Test invalid session ID
#         response = self.app.get('/session/999999')  # Assuming 999999 does not exist
#         self.assertEqual(response.status_code, 404)
#         self.assertIn(b"Session not found", response.data)
    
#     # Add additional tests for edge cases, e.g., invalid query parameters
#     def test_invalid_weight_filter(self):
#         """Test invalid 'filter' query parameter"""
#         response = self.app.get('/weight?from=20230101000000&to=20230101235959&filter=invalid_direction')
#         self.assertEqual(response.status_code, 400)
#         self.assertIn(b"Invalid filter values", response.data)

#     def test_invalid_date_format(self):
#         """Test invalid 'from' date format"""
#         response = self.app.get('/weight?from=2023-01-01&to=20230101235959')
#         self.assertEqual(response.status_code, 400)
#         self.assertIn(b"Invalid 'from' date format", response.data)

#     def test_invalid_date_range(self):
#         """Test 'to' date before 'from' date"""
#         response = self.app.get('/weight?from=20230101235959&to=20230101000000')
#         self.assertEqual(response.status_code, 400)
#         self.assertIn(b"Invalid date range", response.data)

# if __name__ == "__main__":
#     unittest.main()
import unittest
from flask import Flask
from weight_app import app  # Importing the app from weight_app.py
from unittest.mock import patch

class FlaskAppTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Run once before all tests."""
        cls.app = app.test_client()  # Create a test client for your Flask app
        cls.app.testing = True  # Enable testing mode
    
    def test_home_route(self):
        """Test the root route (GET /)"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Truck Weighing API!", response.data)
    
    def test_health_check_route(self):
        """Test the health check route (GET /health)"""
        # Assuming the database is available, if you want to test DB failure, you'd need to mock it
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"OK", response.data)
    
    def test_health_check_failure(self):
        """Test the health check route (GET /health) when DB fails"""
        # Mocking check_db_connection failure (assuming this function is inside weight_app.py)
        with patch('weight_app.check_db_connection', return_value=False):
            response = self.app.get('/health')
            self.assertEqual(response.status_code, 500)
            self.assertIn(b"Failure", response.data)
    
    def test_get_weights_route(self):
        """Test the /weight route (GET /weight) with query params"""
        response = self.app.get('/weight?from=20230101000000&to=20230101235959&filter=in')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # The response should be a list
        
    def test_get_session_route(self):
        """Test the /session/<id> route (GET /session/<id>)"""
        # Simulate a valid session ID (replace 123 with an actual ID in your DB if needed)
        response = self.app.get('/session/123')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # Should return a list of sessions
        
        # Test invalid session ID (replace 999999 with a non-existing ID)
        response = self.app.get('/session/999999')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Session not found", response.data)
    
    def test_invalid_weight_filter(self):
        """Test invalid 'filter' query parameter"""
        response = self.app.get('/weight?from=20230101000000&to=20230101235959&filter=invalid_direction')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid filter values", response.data)

    def test_invalid_date_format(self):
        """Test invalid 'from' date format"""
        response = self.app.get('/weight?from=2023-01-01&to=20230101235959')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid 'from' date format", response.data)

    def test_invalid_date_range(self):
        """Test 'to' date before 'from' date"""
        response = self.app.get('/weight?from=20230101235959&to=20230101000000')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid date range", response.data)

if __name__ == "__main__":
    unittest.main()
