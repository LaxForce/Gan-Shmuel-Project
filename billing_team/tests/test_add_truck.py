import pytest


def test_add_truck_invalid_data():
    # Test with `None` input
    response, status_code = add_truck(None)
    assert response == {"error": "Invalid JSON or empty request body"}
    assert status_code == 400

    # Test with invalid type (e.g., a list)
    response, status_code = add_truck([])
    assert response == {"error": "Invalid JSON or empty request body"}
    assert status_code == 400

    # Test with missing required keys
    response, status_code = add_truck({"id": 1})
    assert response == {"error": "id and provider_id are required"}
    assert status_code == 400

    response, status_code = add_truck({"provider_id": "p1"})
    assert response == {"error": "id and provider_id are required"}
    assert status_code == 400


def add_truck(data):
    if data is None or not isinstance(data, dict):
        return {"error": "Invalid JSON or empty request body"}, 400

    provider_id = data.get('provider_id')
    id = data.get('id')

    if not id or not provider_id:
        return {"error": "id and provider_id are required"}, 400